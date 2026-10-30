# pip install flask joblib pymysql python-dotenv
import os
import joblib
import pymysql  # sqlite3 대신 pymysql 임포트 (pip install pymysql 필요)
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ai_board_model.pkl")
app.json.ensure_ascii = False  # json 응답 시 한글 깨짐 방지

# 🛠️ MariaDB 접속 설정
DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_DATABASE"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor
}

# AI 모델 확인 및 로드
if not os.path.exists(MODEL_PATH):
    print(f"⚠️ [경고] {MODEL_PATH} 파일이 없습니다. 먼저 train_model.py를 실행해 주세요.")
else:
    ai_model = joblib.load(MODEL_PATH)

# DB 연결 헬퍼
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# [DB INIT] DDL 실행: 테이블이 없으면 생성
def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            CREATE TABLE IF NOT EXISTS posts (
                id BIGINT NOT NULL AUTO_INCREMENT,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                regdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            cursor.execute(sql)
        conn.commit()
        print("✅ [DB 초기화] posts 테이블 확인/생성 완료")
    except Exception as e:
        conn.rollback()
        print(f"❌ [DB 초기화 오류] {str(e)}")
        raise
    finally:
        conn.close()

# 앱 시작 시 테이블 초기화
init_db()

# [READ] 메인 페이지 랜더링
@app.route("/")
def index():
    return render_template("index.html")

# [READ] 게시글 목록 조회 API
@app.route("/api/posts", methods=["GET"])
def get_posts():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT id, title, content, DATE_FORMAT(regdate, '%Y-%m-%d %H:%i:%s') AS regdate
            FROM posts
            ORDER BY id DESC
            """
            cursor.execute(sql)
            posts = cursor.fetchall()
    except Exception as e:
        return jsonify({"success": False, "message": f"DB 조회 오류: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify(posts)

# [CREATE] 게시글 등록 API (AI 추론 적용)
@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.json
    title = data.get("title", "")
    content = data.get("content", "")

    if not title or not content:
        return jsonify({"success": False, "message": "제목과 내용을 입력해 주세요."}), 400

    # AI 실시간 추론 (악성 여부 판단)
    try:
        prediction = ai_model.predict([content])[0]
        if prediction == 1:
            return jsonify({
                "success": False,
                "message": "🚨 AI 필터링 시스템: 악성 문맥 또는 비속어가 감지되어 게시글을 등록할 수 없습니다!"
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"AI 추론 오류: {str(e)}"}), 500

    # 정상 글인 경우 MariaDB에 저장
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO posts (title, content) VALUES (%s, %s)"
            cursor.execute(sql, (title, content))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"DB 저장 오류: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify({"success": True, "message": "게시글이 성공적으로 등록되었습니다."})

# [DELETE] 게시글 삭제 API
@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM posts WHERE id = %s"
            cursor.execute(sql, (post_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"DB 삭제 오류: {str(e)}"}), 500
    finally:
        conn.close()

    return jsonify({"success": True, "message": "게시글이 삭제되었습니다."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
