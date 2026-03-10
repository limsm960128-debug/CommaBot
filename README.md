# 📰 뉴스레터 자동화 파이프라인

AI/유통 관련 뉴스를 매일 아침 자동으로 수집하여 Notion 데이터베이스에 업로드하는 파이프라인입니다.

---

## 📁 프로젝트 디렉토리 구조

```
newsletter-pipeline/           ← GitHub 레포 루트
├── main.py                    ← 메인 실행 스크립트
├── requirements.txt           ← Python 의존성
├── README.md                  ← 이 파일
└── .github/
    └── workflows/
        └── schedule.yml       ← GitHub Actions 자동화 설정
```

---

## 🔑 GitHub Secrets 목록

GitHub 레포 → Settings → Secrets and variables → Actions → **New repository secret**

| Secret 이름           | 설명                                              | 발급처 |
|----------------------|--------------------------------------------------|--------|
| `NAVER_CLIENT_ID`    | 네이버 개발자 앱의 Client ID                        | [네이버 개발자센터](https://developers.naver.com) |
| `NAVER_CLIENT_SECRET`| 네이버 개발자 앱의 Client Secret                    | 위 동일 |
| `NOTION_TOKEN`       | Notion Integration의 Internal Integration Token  | [Notion Integrations](https://www.notion.so/my-integrations) |
| `NOTION_DB_ID`       | 노션 데이터베이스 ID (URL에서 추출)                  | Notion DB URL |

---

## 🚀 세팅 가이드 (단계별)

### Step 1 — 네이버 검색 API 발급

1. [네이버 개발자센터](https://developers.naver.com/apps/#/register) 접속 → 애플리케이션 등록
2. **사용 API**: `검색` 선택
3. 환경 추가: `WEB 설정` → 서비스 URL에 `http://localhost` 입력
4. 등록 후 **Client ID**와 **Client Secret** 복사

### Step 2 — Notion Integration 생성

1. [Notion My Integrations](https://www.notion.so/my-integrations) 접속
2. **+ New integration** 클릭
3. 이름 입력 (예: `NewsletterBot`) → Submit
4. **Internal Integration Token** 복사 → `NOTION_TOKEN`으로 저장

### Step 3 — Notion 데이터베이스 설정

1. Notion에서 새 페이지 생성 → `/database` → **Table** 선택
2. 컬럼 구조 설정:

   | 컬럼 이름 | 컬럼 타입 |
   |---------|---------|
   | `이름`   | Title   |
   | `날짜`   | Date    |
   | `링크`   | URL     |

3. DB 페이지 오른쪽 상단 **...** → **+ Add connections** → 방금 만든 Integration 연결
4. DB URL에서 ID 추출:
   ```
   https://www.notion.so/yourworkspace/[여기가-DB-ID]?v=...
   ```
   하이픈 없이 32자리 문자열 → `NOTION_DB_ID`로 저장

### Step 4 — GitHub 레포 설정

1. GitHub에 새 레포지토리 생성 (Private 권장)
2. 위 파일들을 모두 업로드
3. **Settings → Secrets and variables → Actions**에서 4개의 Secret 등록

### Step 5 — 실행 확인

- Actions 탭 → `뉴스레터 자동화 파이프라인` → **Run workflow** 클릭으로 즉시 테스트
- 성공 시 Notion DB에 기사들이 추가된 것을 확인

---

## ⏰ 스케줄 설명

| 항목 | 내용 |
|-----|------|
| 실행 시각 | 매주 월~금 오전 7:00 (KST) |
| cron 표현식 | `0 22 * * 0-4` (UTC 기준) |
| UTC → KST 계산 | KST = UTC + 9시간, 7:00 KST = 전날 22:00 UTC |

---

## 🐛 트러블슈팅

| 오류 | 원인 | 해결 |
|-----|------|------|
| `401 Unauthorized` (Naver) | Client ID/Secret 오류 | Secret 값 재확인 |
| `400 Bad Request` (Notion) | DB 컬럼명 불일치 | `이름`, `날짜`, `링크` 정확히 일치하는지 확인 |
| `403 Forbidden` (Notion) | Integration이 DB에 연결 안 됨 | DB 설정에서 Integration 연결 확인 |
| 기사 수집 0건 | API 할당량 초과 | 네이버 API 일일 25,000건 제한 확인 |
