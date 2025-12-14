import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
import json     # JSON 데이터 처리를 위해 json 모듈 사용
import traceback # 오류 추적을 위해 import

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

# --- 3. 범용 데이터 로딩 함수 (키 매핑 추가) ---
# data_list: 실제 이벤트 데이터 목록 (JSON records)
# cat_id: 삽입할 카테고리 ID (int)
# key_map: JSON 데이터의 키 이름을 DB 필드 이름으로 매핑하는 딕셔너리
def load_data_into_db(data_list, cat_id, key_map):
    if not data_list:
        print("경고: 입력된 데이터 목록이 비어있어 로딩을 건너뜜니다.")
        return 0

    count = 0
    for item in data_list:
        try:
            # 딕셔너리 매핑을 사용하여 데이터 추출
            api_title = item.get(key_map['title'], '제목 없음')
            api_location = item.get(key_map['location'], '위치 미상')
            api_description = item.get(key_map['description'], '') 
            start_date_raw = item.get(key_map['start_date'])
            end_date_raw = item.get(key_map['end_date'])

            if not start_date_raw or not end_date_raw:
                continue

            try:
                # 날짜 문자열을 '%Y-%m-%d' 형식으로 파싱
                start_date = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
            except Exception:
                # 날짜 변환 오류 발생 시 건너뛰기
                continue

            new_event = Event(
                title=api_title,
                description=api_description,
                location=api_location,
                start_date=start_date,
                end_date=end_date,
                category_id=cat_id
            )
            db.session.add(new_event)
            count += 1
            
        except Exception as e:
            # 특정 레코드 처리 중 오류 발생 시 메시지 출력 후 다음 레코드로 진행
            print(f"개별 레코드 처리 중 오류 발생: {e} - 데이터: {item.get(key_map['title'])}")
            
    db.session.commit()
    return count

def load_json_file(filepath):
    """JSON 파일을 로드하고 'records' 키의 데이터를 반환"""
    if not os.path.exists(filepath):
        print(f"경고: 데이터 파일 '{filepath}'을(를) 찾을 수 없어 로딩을 건너뜁니다.")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        return full_data.get('records', [])
    except Exception as e:
        print(f"JSON 파일 '{filepath}' 로딩 중 심각한 오류 발생: {e}")
        traceback.print_exc()
        return None

# --- 4. 초기 DB 생성 및 데이터 설정 함수 (파일 로딩 함수 호출) ---
def init_db():
    db_needs_recreate = not os.path.exists(db_path) or not Category.query.first()

    if os.path.exists(db_path) and not db_needs_recreate:
        # DB 구조가 변경되었다면 삭제하고 새로 만듦 (카테고리 변경 시 강제 적용)
        # 이전에 init_db에서 삭제 로직을 넣었으므로, 여기서는 카테고리 맵을 확인하여 진행
        category_count = Category.query.count()
        if category_count != 5: # 현재 기대하는 카테고리 수 (축제, 팝업, 할인, 전시, 공연)
             os.remove(db_path)
             db_needs_recreate = True
             print(f"기존 DB 파일 삭제 완료. (카테고리 수 불일치: {category_count} != 5)")

    if db_needs_recreate or not Event.query.first():
        print("데이터베이스 파일을 새로 생성 및 초기화합니다.")
        with app.app_context():
            db.create_all()

            # 초기 카테고리 데이터 삽입
            categories_list = ['축제', '팝업 스토어', '할인 행사', '전시', '공연'] 
            for name in categories_list:
                if not Category.query.filter_by(category_name=name).first():
                    cat = Category(category_name=name)
                    db.session.add(cat)
            
            db.session.commit()
            print("초기 카테고리 데이터 삽입 완료.")
            
            category_map = {cat.category_name: cat.category_id for cat in Category.query.all()}

            # ------------------------------------------------------------
            # 1. '축제' 데이터 로딩
            # ------------------------------------------------------------
            
            # DB의 '축제' 카테고리 ID 가져오기
            festival_cat_id = category_map.get('축제')
            
            # JSON 키 매핑 (기존 축제 데이터)
            festival_key_map = {
                'title': '축제명',
                'location': '개최장소',
                'start_date': '축제시작일자',
                'end_date': '축제종료일자',
                'description': '축제내용'
            }
            
            festival_data = load_json_file('전국문화축제표준데이터.json')
            if festival_data and festival_cat_id is not None:
                count = load_data_into_db(festival_data, festival_cat_id, festival_key_map)
                print(f"'{festival_key_map['title']}' 파일에서 이벤트 데이터 {count}개 삽입 완료. (카테고리: 축제)")

            # ------------------------------------------------------------
            # 2. '공연' 데이터 로딩
            # ------------------------------------------------------------
            
            # DB의 '공연' 카테고리 ID 가져오기
            performance_cat_id = category_map.get('공연')
            
            # JSON 키 매핑 (새로운 공연 데이터)
            performance_key_map = {
                'title': '행사명',
                'location': '장소',
                'start_date': '행사시작일자',
                'end_date': '행사종료일자',
                'description': '행사내용'
            }
            
            performance_data = load_json_file('전국공연행사정보표준데이터.json')
            if performance_data and performance_cat_id is not None:
                count = load_data_into_db(performance_data, performance_cat_id, performance_key_map)
                print(f"'{performance_key_map['title']}' 파일에서 이벤트 데이터 {count}개 삽입 완료. (카테고리: 공연)")
            
    else:
        print("기존 데이터베이스 파일을 사용합니다.")


# --- 5. Flask 라우팅 (웹페이지 URL 처리) 설정 ---
@app.route('/')
def event_list():
    categories = Category.query.all()
    today = datetime.today().date()
    
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
            db.session.commit()
            return redirect(url_for('event_detail', event_id=event.event_id))
        except Exception as e:
            db.session.rollback()
            return f"이벤트 수정 오류 발생: {e}", 500

@app.route('/delete/<int:event_id>', methods=['POST'])
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        return redirect(url_for('event_list'))
    except Exception as e:
        db.session.rollback()
        return f"이벤트 삭제 오류 발생: {e}", 500


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)