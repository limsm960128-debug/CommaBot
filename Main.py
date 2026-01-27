import requests
import json
import os
import random

# 깃허브 금고(Secrets)에서 키를 꺼내오는 코드입니다.
GEMINI_API_KEY = os.environ['GEMINI_API_KEY']
KAKAO_API_KEY = os.environ['KAKAO_API_KEY']
KAKAO_REFRESH_TOKEN = os.environ['KAKAO_REFRESH_TOKEN']

# ==========================================
# 🔄 토큰 갱신 (리프레시 토큰으로 액세스 토큰 받기)
# ==========================================
def get_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_API_KEY,
        "refresh_token": KAKAO_REFRESH_TOKEN
    }
    try:
        res = requests.post(url, data=data)
        tokens = res.json()
        if "access_token" in tokens:
            return tokens["access_token"]
        else:
            print(f"❌ 토큰 발급 실패: {tokens}")
            return None
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return None

# ==========================================
# 🧠 AI 질문 생성기 (Gemini 1.5 Flash)
# ==========================================
def call_gemini_api(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {'Content-Type': 'application/json'}
    params = {'key': GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.0, "maxOutputTokens": 600}
    }
    try:
        response = requests.post(url, headers=headers, params=params, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        pass
    return None

def get_ai_message():
    topics = [
        "중국 공장 MOQ 협상 이메일 팁", "알리바바 소싱 이미지 분석 팁", "불량 클레임 리포트 작성법",
        "신제품 아이디어 브레인스토밍", "경쟁사 리뷰 분석 팁", "선적 서류 오타 검증 팁",
        "HS CODE 분류 추천 팁", "상세페이지 구매 전환율 카피", "원가 계산 엑셀 함수 팁",
        "해외 전시회 트렌드 요약 팁", "패키지 디자인 프롬프트 팁", "샘플 피드백 영문 메일 팁",
        "시즌 상품 스케줄링 팁", "KC 인증 규제 요약 팁", "환율 변동 마진 분석 팁"
    ]
    topic = random.choice(topics)
    prompt = f"""
    당신은 생활용품 소싱 전문가입니다. 주제: '{topic}'
    3~10년차 실무자에게 AI를 활용해 시간을 단축시킬 수 있는 '행동 유도형 질문' 하나와
    'AI에게 입력할 명령어 예시'를 작성해주세요.
    형식: [💡 Comma Bot의 인사이트] (내용) (명령어 예시)
    """
    result = call_gemini_api(prompt)
    if result: return result
    
    # 비상용 메시지
    return "[💡 Comma Bot의 인사이트]\n오늘 반복되는 엑셀 작업이 있나요?\nAI에게 '이거 자동화 매크로 짜줘'라고 물어보세요."

# ==========================================
# 🚀 실행
# ==========================================
def run_bot():
    print("🚀 Comma Bot 자동 실행 중...")
    token = get_access_token()
    if not token: return

    message = get_ai_message()
    
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"template_object": json.dumps({
        "object_type": "text",
        "text": message,
        "link": {"web_url": "https://gemini.google.com", "mobile_web_url": "https://gemini.google.com"},
        "button_title": "AI로 업무 시간 줄이기"
    })}
    
    res = requests.post(url, headers=headers, data=data)
    if res.json().get('result_code') == 0:
        print("🎉 전송 성공!")
    else:
        print(f"❌ 전송 실패: {res.json()}")

if __name__ == "__main__":
    run_bot()
