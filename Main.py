"""
뉴스레터 자동화 파이프라인
- 네이버 뉴스 API로 AI/유통 관련 뉴스 수집
- Notion 데이터베이스에 자동 업로드
"""

import os
import re
import requests
from datetime import datetime, timezone, timedelta

# ============================================================
# 0. 환경 변수 로드
#    GitHub Secrets에서 주입된 값들을 가져옵니다.
# ============================================================
NAVER_CLIENT_ID     = os.environ["NAVER_CLIENT_ID"]
NAVER_CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]
NOTION_TOKEN        = os.environ["NOTION_TOKEN"]
NOTION_DB_ID        = os.environ["NOTION_DB_ID"]

# ============================================================
# 1. 검색 설정
# ============================================================
SEARCH_QUERIES = [
    "유통 AI",
    "리테일 테크",
    "이커머스 AI",
    "소싱 AI",
    "직장인 AI",
]
DISPLAY_COUNT = 5   # 검색어당 최대 결과 수
SORT_BY       = "date"  # date = 최신순, sim = 관련도순


# ============================================================
# 2. 유틸리티 함수
# ============================================================

def clean_html_tags(text: str) -> str:
    """
    HTML 태그(<b>, </b>, &amp; 등 HTML 엔티티)를 제거하고
    깨끗한 텍스트만 반환합니다.
    """
    # <b>, </b>, <strong> 등 모든 HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)
    # HTML 엔티티 변환 (&amp; → &, &quot; → " 등)
    text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    return text.strip()


def parse_pub_date(pub_date_str: str) -> str:
    """
    네이버 API가 반환하는 날짜 문자열(RFC 2822)을 Notion 날짜 형식(ISO 8601)으로 변환합니다.
    예: 'Mon, 10 Mar 2025 07:00:00 +0900' → '2025-03-10'
    파싱 실패 시 오늘 날짜를 반환합니다.
    """
    try:
        # RFC 2822 → datetime 파싱
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        # 파싱 실패 시 한국 시간(KST) 기준 오늘 날짜 반환
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst).strftime("%Y-%m-%d")


# ============================================================
# 3. 네이버 뉴스 API 호출
# ============================================================

def fetch_naver_news(query: str) -> list[dict]:
    """
    네이버 검색 API(뉴스)를 호출하여 기사 목록을 반환합니다.
    실패 시 빈 리스트를 반환하고 계속 진행합니다.

    반환 형식:
        [{"title": str, "link": str, "pub_date": str}, ...]
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query":   query,
        "display": DISPLAY_COUNT,
        "sort":    SORT_BY,
    }

    print(f"  [Naver] 검색 중: '{query}'")
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # HTTP 에러 시 예외 발생
        data = response.json()

        articles = []
        for item in data.get("items", []):
            articles.append({
                "title":    clean_html_tags(item.get("title", "")),
                "link":     item.get("link") or item.get("originallink", ""),
                "pub_date": parse_pub_date(item.get("pubDate", "")),
            })

        print(f"  [Naver] '{query}' → {len(articles)}건 수집 완료")
        return articles

    except requests.exceptions.HTTPError as e:
        print(f"  [Naver ERROR] HTTP 오류 발생 (query='{query}'): {e}")
    except requests.exceptions.Timeout:
        print(f"  [Naver ERROR] 요청 시간 초과 (query='{query}')")
    except requests.exceptions.RequestException as e:
        print(f"  [Naver ERROR] 요청 실패 (query='{query}'): {e}")
    except Exception as e:
        print(f"  [Naver ERROR] 예상치 못한 오류 (query='{query}'): {e}")

    return []  # 실패해도 다음 검색어로 계속 진행


# ============================================================
# 4. Notion API 업로드
# ============================================================

def upload_to_notion(article: dict) -> bool:
    """
    Notion 데이터베이스에 기사 1건을 업로드합니다.
    성공 여부(True/False)를 반환합니다.

    Notion DB 컬럼 구조:
        - '이름'  : title 타입  → 기사 제목
        - '날짜'  : date  타입  → 발행일
        - '링크'  : url   타입  → 원문 링크
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": "2022-06-28",  # Notion API 버전 고정
    }

    # Notion API 페이로드 구성
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            # [필수] 타이틀 컬럼 — DB의 '이름' 컬럼
            "이름": {
                "title": [
                    {"text": {"content": article["title"][:200]}}  # 최대 200자
                ]
            },
            # 날짜 컬럼 — DB의 '날짜' 컬럼
            "날짜": {
                "date": {"start": article["pub_date"]}
            },
            # URL 컬럼 — DB의 '링크' 컬럼
            "링크": {
                "url": article["link"] if article["link"] else None
            },
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        print(f"  [Notion] 업로드 성공: {article['title'][:50]}...")
        return True

    except requests.exceptions.HTTPError as e:
        # 상세 오류 메시지 출력 (Notion이 이유를 JSON으로 반환함)
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        print(f"  [Notion ERROR] HTTP 오류: {e} | 상세: {detail}")
    except requests.exceptions.Timeout:
        print(f"  [Notion ERROR] 업로드 시간 초과: {article['title'][:50]}")
    except Exception as e:
        print(f"  [Notion ERROR] 예상치 못한 오류: {e}")

    return False


# ============================================================
# 5. 중복 제거 헬퍼
# ============================================================

def deduplicate(articles: list[dict]) -> list[dict]:
    """
    동일한 링크의 기사를 제거합니다.
    링크가 없는 기사는 제목 기준으로 중복 체크합니다.
    """
    seen = set()
    unique = []
    for art in articles:
        key = art["link"] or art["title"]
        if key not in seen:
            seen.add(key)
            unique.append(art)
    return unique


# ============================================================
# 6. 메인 실행 흐름
# ============================================================

def main():
    kst = timezone(timedelta(hours=9))
    now_str = datetime.now(kst).strftime("%Y-%m-%d %H:%M KST")
    print("=" * 60)
    print(f"뉴스레터 자동화 파이프라인 시작: {now_str}")
    print("=" * 60)

    # Step 1: 모든 검색어에 대해 뉴스 수집
    print("\n[STEP 1] 네이버 뉴스 수집")
    all_articles = []
    for query in SEARCH_QUERIES:
        articles = fetch_naver_news(query)
        all_articles.extend(articles)

    print(f"\n  총 수집 기사 수 (중복 포함): {len(all_articles)}건")

    # Step 2: 중복 제거
    unique_articles = deduplicate(all_articles)
    print(f"  중복 제거 후 기사 수: {len(unique_articles)}건")

    if not unique_articles:
        print("\n  수집된 기사가 없습니다. 파이프라인을 종료합니다.")
        return

    # Step 3: Notion 업로드
    print("\n[STEP 2] Notion 데이터베이스 업로드")
    success_count = 0
    fail_count    = 0

    for article in unique_articles:
        ok = upload_to_notion(article)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    # Step 4: 결과 요약
    print("\n" + "=" * 60)
    print(f"파이프라인 완료")
    print(f"  - 업로드 성공: {success_count}건")
    print(f"  - 업로드 실패: {fail_count}건")
    print("=" * 60)


if __name__ == "__main__":
    main()
