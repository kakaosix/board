import os
import sqlite3
import joblib
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "board.db")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ai_board_model.pkl")

# DB 초기화 함수 (테이블 생성)
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.commit()

# 초기 구동 시 DB 생성 및 AI 모델 확인
init_db()
if not os.path.exists(MODEL_PATH):
    print(f"⚠️ [경고] {MODEL_PATH} 파일이 없습니다. 먼저 train_model.py를 실행해 주세요.")
else:
    ai_model = joblib.load(MODEL_PATH)

# [READ] 메인 페이지 랜더링
@app.route("/")
def index():
    return render_template("index.html")

# [READ] 게시글 목록 조회 API
@app.route("/api/posts", methods=["GET"])
def get_posts():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content FROM posts ORDER BY id DESC")
        posts = [{"id": row[0], "title": row[1], "content": row[2]} for row in cursor.fetchall()]
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
        # 1이면 악성, 0이면 정상
        prediction = ai_model.predict([content])[0]
        if prediction == 1:
            return jsonify({
                "success": False, 
                "message": "🚨 AI 필터링 시스템: 악성 문맥 또는 비속어가 감지되어 게시글을 등록할 수 없습니다!"
            }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"AI 추론 오류: {str(e)}"}), 500

    # 정상 글인 경우 데이터베이스(온프레미스 DB)에 저장
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
        conn.commit()

    return jsonify({"success": True, "message": "게시글이 성공적으로 등록되었습니다."})

# [DELETE] 게시글 삭제 API
@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
    return jsonify({"success": True, "message": "게시글이 삭제되었습니다."})

if __name__ == "__main__":
    # 로컬 온프레미스 환경 5000번 포트로 서버 가동
    app.run(host="127.0.0.1", port=5000, debug=True)
