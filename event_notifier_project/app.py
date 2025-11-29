import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Flask 앱 초기 설정
app = Flask(__name__)

#SQLite 데이터베이스 파일 경로 설정
app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite://event_db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#SQLAlchemy 객체 초기화
db = SQLAlchemy(app)

# 데이터베이스 모델 정의

# Category 테이블 (이벤트 분류 기준, 1:N 관계의 '1')
class Category(db.Model):
    # 테이블 이름 정의
    __tablename__ = 'category'
    
    # 필드 정의
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)
    
    # 'Event' 테이블과의 관계 설정 (이 카테고리에 속한 이벤트들을 조회할 때 사용)
    events = db.relationship('Event', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.category_name}>'

# Event 테이블 (구체적인 이벤트 정보, M:N 관계의 'N')
class Event(db.Model):
    # 테이블 이름 정의
    __tablename__ = 'event'

    # 필드 정의
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=False)
    
    # 핵심 필드: 시작일과 종료일 (날짜 기반 쿼리에 사용됨)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    # Category 테이블의 Primary Key를 참조하는 Foreign Key
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)

    def __repr__(self):
        return f'<Event {self.title}>'

# --- 3. 초기 데이터 설정 및 DB 생성 함수 ---
def init_db():
    # 데이터베이스 파일이 이미 존재하는지 확인하고, 없다면 새로 생성 및 초기화합니다.
    db_path = os.path.join(app.root_path, 'event_db.sqlite')
    
    if not os.path.exists(db_path):
        print("데이터베이스 파일을 새로 생성합니다.")
        with app.app_context():
            # 모든 테이블 생성 (Category, Event)
            db.create_all()

            # 초기 카테고리 데이터 삽입 (미리 넣어두기로 한 데이터)
            categories = ['축제', '팝업 스토어', '할인 행사', '전시/공연']
            for name in categories:
                # 이미 데이터가 존재한다면 건너뛰기
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
    # 간단한 HTML을 렌더링할 예정입니다. (다음 단계에서 HTML 파일 추가)
    
    # 모든 카테고리 정보 조회 (필터링 메뉴에 사용)
    categories = Category.query.all()
    
    # 모든 이벤트 정보 조회 (나중에는 날짜 필터링 쿼리를 추가할 예정)
    events = Event.query.all() 
    
    # 'index.html' 템플릿에 데이터 전달
    return render_template('index.html', events=events, categories=categories)


if __name__ == '__main__':
    # Flask 앱 컨텍스트 내에서 DB 초기화 함수 실행
    with app.app_context():
        init_db()
    
    # Flask 앱 실행 (디버그 모드 ON)
    app.run(debug=True)