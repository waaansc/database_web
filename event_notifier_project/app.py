import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy

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
    # Event와의 관계 설정
    events = db.relationship('Event', backref='category', lazy=True)
    def __repr__(self):
        return f'<Category {self.category_name}>'

class Event(db.Model):
    __tablename__ = 'event'
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    # 핵심 필드: 날짜 기반 쿼리에 사용됨
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    # Category 테이블의 Primary Key를 참조하는 Foreign Key
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    def __repr__(self):
        return f'<Event {self.title}>'

# --- 3. 초기 DB 생성 및 데이터 설정 함수 ---
def init_db():
    if not os.path.exists(db_path):
        print("데이터베이스 파일을 새로 생성합니다.")
        with app.app_context():
            db.create_all()

            # 초기 카테고리 데이터 삽입 (미리 넣어두기로 한 데이터)
            categories = ['축제', '팝업 스토어', '할인 행사', '전시/공연']
            for name in categories:
                if not Category.query.filter_by(category_name=name).first():
                    cat = Category(category_name=name)
                    db.session.add(cat)
            
            db.session.commit()
            print("초기 카테고리 데이터 삽입 완료.")
    else:
        print("기존 데이터베이스 파일을 사용합니다.")

# --- 4. Flask 라우팅 (웹페이지 URL 처리) 설정 ---

# 메인 페이지 (CRUD의 Read 기능: 날짜 기반 필터링 조회)
@app.route('/')
def event_list():
    categories = Category.query.all()
    today = datetime.today().date()
    
    # DB 활용 핵심: 오늘 날짜(today)를 기준으로 종료일이 오늘이거나 미래인 이벤트만 조회
    # SQL 쿼리: SELECT * FROM event WHERE end_date >= TODAY ORDER BY start_date ASC
    events = Event.query.filter(
        Event.end_date >= today
    ).order_by(Event.start_date.asc()).all() 
    
    return render_template('index.html', events=events, categories=categories, today=today)


# 이벤트 등록 페이지 (CRUD의 Create 기능)
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

            new_event = Event(
                title=title, description=description, location=location,
                start_date=start_date, end_date=end_date, category_id=category_id
            )
            db.session.add(new_event)
            db.session.commit() # SQL INSERT 실행

            return redirect(url_for('event_list'))
        
        except Exception as e:
            db.session.rollback()
            return f"이벤트 등록 오류 발생: {e}", 500

# 이벤트 상세/수정 페이지 (CRUD의 Read One 및 Update 기능)
@app.route('/<int:event_id>', methods=['GET', 'POST'])
def event_detail(event_id):
    # event_id를 사용하여 DB에서 해당 이벤트 레코드를 조회 (CRUD-R)
    event = Event.query.get_or_404(event_id)
    categories = Category.query.all()
    
    if request.method == 'GET':
        # GET 요청 시 상세 정보와 수정 폼이 포함된 detail.html을 보여줌
        return render_template('detail.html', event=event, categories=categories)

    elif request.method == 'POST':
        # POST 요청 시 이벤트 정보를 수정합니다. (CRUD-U)
        try:
            # 폼에서 수정된 데이터 가져오기
            event.title = request.form['title']
            event.description = request.form.get('description', '')
            event.location = request.form['location']
            
            # 날짜 형식 변환 및 업데이트
            event.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            event.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            event.category_id = int(request.form['category_id'])

            # DB 세션 커밋 (SQL UPDATE 실행)
            db.session.commit()
            
            # 수정 후 상세 페이지로 리디렉션
            return redirect(url_for('event_detail', event_id=event.event_id))
        
        except Exception as e:
            db.session.rollback()
            return f"이벤트 수정 오류 발생: {e}", 500

# 이벤트 삭제 기능 (CRUD의 Delete 기능)
@app.route('/delete/<int:event_id>', methods=['POST'])
def event_delete(event_id):
    # event_id를 사용하여 DB에서 해당 이벤트 레코드를 조회
    event = Event.query.get_or_404(event_id)
    
    try:
        # DB 세션에서 객체 삭제
        db.session.delete(event)
        # DB 커밋 (SQL DELETE 실행)
        db.session.commit()
        
        # 삭제 후 메인 목록 페이지로 리디렉션
        return redirect(url_for('event_list'))
        
    except Exception as e:
        db.session.rollback()
        return f"이벤트 삭제 오류 발생: {e}", 500


if __name__ == '__main__':
    with app.app_context():
        # DB 초기화 함수 실행
        init_db()
    
    app.run(debug=True)