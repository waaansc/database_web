# 📅 기간 한정 이벤트 알림 웹 애플리케이션 (database_web)

공공데이터를 활용하여 **지역·기간 한정 이벤트를 관리하고 조회할 수 있는 웹 애플리케이션**입니다.  
Flask와 SQLite를 기반으로 하며, 이벤트를 **카테고리별로 CRUD(Create / Read / Update / Delete)** 할 수 있도록 구현했습니다.

---

## 🔧 기술 스택

- **Backend**: Python, Flask  
- **Template Engine**: Jinja2  
- **Database / ORM**: SQLite, Flask-SQLAlchemy  
- **Frontend**: HTML, CSS, JavaScript (Vanilla)

---

## 📁 프로젝트 구조

```text
database_web/
└─ event_notifier_project/
   ├─ app.py                 # Flask 메인 애플리케이션
   ├─ event_db.sqlite        # SQLite DB (공공데이터 JSON 기반 생성)
   ├─ templates/
   │  ├─ index.html          # 이벤트 목록 페이지 (Read)
   │  ├─ create.html         # 이벤트 등록 페이지 (Create)
   │  └─ detail.html         # 이벤트 상세 / 수정 / 삭제 (Read, Update, Delete)
   └─ *.json                 # 공공데이터 JSON 원본 (초기 DB 생성용)
```

---

## 🗂 데이터베이스 구조

### Category 테이블

| 컬럼명 | 타입 | 설명 |
|------|------|------|
| category_id | Integer (PK) | 카테고리 ID |
| category_name | String | 카테고리 이름 |

### Event 테이블

| 컬럼명 | 타입 | 설명 |
|------|------|------|
| event_id | Integer (PK) | 이벤트 ID |
| title | String | 이벤트 제목 |
| description | Text | 이벤트 설명 |
| location | String | 장소 |
| start_date | Date | 시작일 |
| end_date | Date | 종료일 |
| category_id | Integer (FK) | 카테고리 ID |

- **관계**: Category (1) : Event (N)

---

## 📊 데이터 출처 (공공데이터 활용)

본 프로젝트의 데이터베이스(`event_db.sqlite`)는 아래 **공공데이터포털** 자료를 기반으로 자동 생성됩니다.

- 전국문화축제표준데이터.json  
- 전국공연행사정보표준데이터.json  

출처: 공공데이터포털  
https://www.data.go.kr

### DB 생성 방식
1. Flask 앱 최초 실행
2. SQLite DB 자동 생성
3. 기본 카테고리(축제, 팝업 스토어, 할인 행사, 전시, 공연) 삽입
4. JSON 파일의 `records` 데이터를 파싱하여 이벤트 데이터로 저장

---

## 🧩 주요 기능

- 이벤트 목록 조회 (D-Day 표시)
- 이벤트 등록 / 수정 / 삭제
- 카테고리 기반 이벤트 관리
- SQLite + ORM 기반 데이터 처리

---

## 🌐 URL 라우팅 구조

| URL | Method | 설명 |
|----|--------|------|
| `/` | GET | 이벤트 목록 조회 |
| `/new` | GET / POST | 이벤트 등록 |
| `/<event_id>` | GET / POST | 상세 조회 및 수정 |
| `/delete/<event_id>` | POST | 이벤트 삭제 |

---

## ▶ 실행 방법

###  1. 가상환경 생성 및 활성화 (venv)

```bash
cd event_notifier_project
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```
###  2. 확장 설치하기

```bash
pip install flask
pip install flaskalchemy
```
### 3. 애플리케이션 실행

```bash
python app.py
```

- 최초 실행 시 DB 및 초기 데이터 자동 생성  
- 애플리케이션 실행 시 로컬 환경에서 웹 확인 가능

---

## 📄 라이선스

- 학습 및 과제용 프로젝트
- 공공데이터는 각 데이터의 이용 약관을 따릅니다.
