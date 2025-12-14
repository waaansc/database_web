import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import json     # JSON 데이터 처리를 위해 json 모듈 사용

# --- 1. Flask 앱 초기 설정 및 DB 경로 설정 ---
app = Flask(__name__)

# SQLite 데이터베이스 파일 경로 설정
db_path = os.path.join(app.root_path, 'event_db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 객체 초기화
db = SQLAlchemy()

# 명시적으로 Flask 앱에 DB 설정 연결 (오류 방지)
with app.app_context():
    db.init_app(app)

# --- 2. 데이터베이스 모델 정의 ---
class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)
    events = db.relationship('Event', backref='category', lazy=True)
    def __repr__(self):
        return f'<Category {self.category_name}>'

class Event(db.Model):
    __tablename__ = 'event'
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    def __repr__(self):
        return f'<Event {self.title}>'

# --- 3. 파일 기반 데이터 로딩 함수 (JSON 전용) ---
# NOTE: 이 함수는 '전국문화축제표준데이터.json' 파일에 맞춰 작성되었습니다.
def load_data_from_file(filepath):
    if not os.path.exists(filepath):
        print(f"경고: 데이터 파일 '{filepath}'을(를) 찾을 수 없어 로딩을 건너뜁니다.")
        return

    try:
        # 1. JSON 파일 로딩 및 'records' 리스트 추출
        with open(filepath, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        
        # JSON 구조에서 'records' 키의 리스트를 추출
        data_list = full_data.get('records', [])
        
        if not data_list:
            print(f"경고: JSON 파일 '{filepath}'에서 'records' 데이터를 찾을 수 없어 로딩을 건너뜁니다.")
            return

        # 2. Category 이름으로 ID를 찾는 맵 준비
        category_map = {cat.category_name: cat.category_id for cat in Category.query.all()}
        
        # 사용자 요청: 모든 데이터를 '축제' 카테고리에 넣음
        cat_id = category_map.get('축제')
        if cat_id is None:
            print("오류: '축제' 카테고리를 DB에서 찾을 수 없습니다. DB 초기화 확인 필요.")
            return

        count = 0
        for item in data_list:
            # 3. 데이터 정제 및 DB 삽입 (사용자 요청 필드 매핑)
            
            # 원본 JSON 필드 이름 -> DB 필드 이름 매핑
            api_title = item.get('축제명', '제목 없음')
            api_location = item.get('개최장소', '위치 미상')
            api_description = item.get('축제내용', '') 
            
            # 날짜 필드 추출
            start_date_raw = item.get('축제시작일자')
            end_date_raw = item.get('축제종료일자')

            if not start_date_raw or not end_date_raw:
                continue

            # 4. 날짜 형식 변환 (YYYY-MM-DD 형식)
            try:
                # '2025-06-27' 형식의 문자열을 datetime.date 객체로 변환
                start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
            except Exception:
                # 날짜 변환 오류 발생 시 건너뜁니다.
                continue

            # 5. DB에 저장 (CRUD-C)
            new_event = Event(
                title=api_title,
                description=api_description,
                location=api_location,
                start_date=start_date,
                end_date=end_date,
                category_id=cat_id # '축제' 카테고리 ID 사용
            )
            db.session.add(new_event)
            count += 1
            
        db.session.commit()
        print(f"JSON 파일('{filepath}')을(를) 통해 이벤트 데이터 {count}개 삽입 완료.")

    except Exception as e:
        db.session.rollback()
        print(f"데이터 로딩 중 심각한 오류 발생: {e}")


# --- 4. 초기 DB 생성 및 데이터 설정 함수 (파일 로딩 함수 호출) ---
def init_db():
    # 이전에 생성된 DB 파일이 있으면 삭제하여 초기화합니다.
    # 기존 DB를 사용하고 싶다면 아래 주석을 제거하지 마세요.
    # if os.path.exists(db_path):
    #     os.remove(db_path) 
    
    if not os.path.exists(db_path) or not Event.query.first():
        print("데이터베이스 파일을 새로 생성 및 초기화합니다.")
        with app.app_context():
            db.create_all()

            # 초기 카테고리 데이터 삽입 (Category ID가 1부터 시작합니다)
            categories = ['축제', '팝업 스토어', '할인 행사', '전시/공연']
            for name in categories:
                if not Category.query.filter_by(category_name=name).first():
                    cat = Category(category_name=name)
                    db.session.add(cat)
            
            db.session.commit()
            print("초기 카테고리 데이터 삽입 완료.")
            
            # --- JSON 데이터 로딩 함수 호출 ---
            # 사용자님이 업로드하신 파일 이름을 사용합니다.
            load_data_from_file('전국문화축제표준데이터.json')
            
    else:
        print("기존 데이터베이스 파일을 사용합니다. (이벤트 목록에 데이터가 이미 있을 수 있습니다.)")

# --- 5. Flask 라우팅 (웹페이지 URL 처리) 설정 ---
@app.route('/')
def event_list():
    categories = Category.query.all()
    today = datetime.today().date()
    
    # SQL: SELECT * FROM event WHERE end_date >= TODAY ORDER BY start_date ASC
    events = Event.query.filter(Event.end_date >= today).order_by(Event.start_date.asc()).all() 
    
    return render_template('index.html', events=events, categories=categories, today=today)

@app.route('/new', methods=['GET', 'POST'])
def event_create():
    categories = Category.query.all()
    if request.method == 'GET':
        return render_template('create.html', categories=categories)
    elif request.method == 'POST':
        try:
            title = request.form['title']
            description = request.form.get('description', '')
            location = request.form['location']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            category_id = int(request.form['category_id'])
            new_event = Event(title=title, description=description, location=location, start_date=start_date, end_date=end_date, category_id=category_id)
            db.session.add(new_event)
            db.session.commit()
            return redirect(url_for('event_list'))
        except Exception as e:
            db.session.rollback()
            return f"이벤트 등록 오류 발생: {e}", 500

@app.route('/<int:event_id>', methods=['GET', 'POST'])
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    categories = Category.query.all()
    if request.method == 'GET':
        return render_template('detail.html', event=event, categories=categories)
    elif request.method == 'POST':
        try:
            event.title = request.form['title']
            event.description = request.form.get('description', '')
            event.location = request.form['location']
            event.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            event.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            event.category_id = int(request.form['category_id'])
            # SQL: UPDATE event SET ... WHERE event_id = [요청 ID]
            db.session.commit()
            return redirect(url_for('event_detail', event_id=event.event_id))
        except Exception as e:
            db.session.rollback()
            return f"이벤트 수정 오류 발생: {e}", 500

@app.route('/delete/<int:event_id>', methods=['POST'])
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        # SQL: DELETE FROM event WHERE event_id = [요청 ID]
        db.session.delete(event)
        db.session.commit()
        return redirect(url_for('event_list'))
    except Exception as e:
        db.session.rollback()
        return f"이벤트 삭제 오류 발생: {e}", 500

if __name__ == '__main__':
    with app.app_context():
        # DB가 초기화될 때 데이터 로딩 함수가 호출됩니다.
        init_db()
    app.run(debug=True)