import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# --- 1. Flask 앱 초기 설정 및 DB 경로 설정 ---
app = Flask(__name__)

# SQLite 데이터베이스 파일 경로 설정 (DB 파일 위치 지정)
db_path = os.path.join(app.root_path, 'event_db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 객체 초기화
db = SQLAlchemy()

# 명시적으로 Flask 앱에 DB 설정 연결 (이전 RuntimeError 해결을 위한 방식)
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

# --- 3. 초기 데이터 설정 및 DB 생성 함수 ---
def init_db():
    if not os.path.exists(db_path):
        print("데이터베이스 파일을 새로 생성합니다.")
        with app.app_context():
            db.create_all()

            # 초기 카테고리 데이터 삽입
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

# 메인 페이지 (CRUD의 Read 기능: 이벤트 목록 조회)
@app.route('/')
def event_list():
    categories = Category.query.all()
    # 날짜 기반 동적 쿼리 : 오늘 날짜를 기준으로 종료일이 오늘보다 크거나 같은 이벤트만 조회
    today = datetime.today().date()
    events = Event.query.filter(
        Event.end_date >= today # 종료일이 오늘이거나 미래인 이벤트
    ).order_by(
        Event.start_date.asc() # 사직일이 빠른 순서대로 정렬
    ).all()

    #index.html 템플릿에 데이터 전달
    return render_template('index.html', events = events, categories = categories)

# 이벤트 등록 페이지 (CRUD의 Create 기능)
@app.route('/new', methods=['GET', 'POST'])
def event_create():
    # 등록 폼에서 사용할 카테고리 목록을 DB에서 가져옵니다.
    categories = Category.query.all()
    
    # GET 요청: 폼 페이지를 보여줍니다.
    if request.method == 'GET':
        return render_template('create.html', categories=categories)

    # POST 요청: 폼 데이터를 받아 DB에 저장합니다.
    elif request.method == 'POST':
        try:
            # 1. 폼 데이터 가져오기 및 날짜 형식 변환
            title = request.form['title']
            description = request.form['description']
            location = request.form['location']
            # HTML 폼에서 받은 'YYYY-MM-DD' 문자열을 Python의 datetime.date 객체로 변환합니다.
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            category_id = int(request.form['category_id'])

            # 2. 새로운 Event 객체 생성 및 DB에 추가 (SQL INSERT 준비)
            new_event = Event(
                title=title,
                description=description,
                location=location,
                start_date=start_date,
                end_date=end_date,
                category_id=category_id
            )
            db.session.add(new_event)
            db.session.commit() # SQL INSERT 실행

            # 등록 후 메인 페이지로 이동합니다.
            return redirect(url_for('event_list'))
        
        except Exception as e:
            # 오류 발생 시 (예: 날짜 형식이 잘못되었을 때)
            return f"이벤트 등록 오류 발생: {e}", 500


if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    app.run(debug=True)