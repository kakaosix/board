# pip install flask scikit-learn numpy joblib
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import os

# 1. 간단한 가상 학습 데이터 (0: 정상/긍정, 1: 악성/부정)
train_data = [
    # 정상 데이터
    ("안녕하세요 반가워요", 0),
    ("오늘 날씨가 정말 좋네요", 0),
    ("유익한 정보 감사합니다", 0),
    ("추천합니다 좋은 글이네요", 0),
    
    # 악성 데이터
    ("바보 멍청이 짜증나네", 1),
    ("진짜 최악이다 쓰레기 같아", 1),
    ("꺼져라 보기 싫다 광고", 1),
    ("이게 무슨 글이냐 한심하다", 1)
]

# 데이터 분리
X_train = [text for text, label in train_data]
y_train = [label for text, label in train_data]

# 2. 파이프라인 구축 (텍스트 벡터화 + 나이브 베이즈 분류기)
model = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

# 3. 모델 학습
print("AI 모델 학습을 시작합니다...")
model.fit(X_train, y_train)

# 4. 학습된 모델 및 벡터라이저 저장 (온프레미스 서버 내에 파일로 보관)
joblib.dump(model, os.path.join(os.path.dirname(__file__), "ai_board_model.pkl"))
print("모델 저장 완료! (ai_board_model.pkl)")
