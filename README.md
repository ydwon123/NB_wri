## 블로그 초안 생성기 (OpenAI / Claude)

첨부한 자료(여러 파일·폴더)를 바탕으로, 목적에 맞는 블로그 초안을 OpenAI 또는 Claude API로 생성하는 간단한 도구입니다. CLI와 GUI 모두 제공합니다.

### GUI 실행
```bash
python -m src.gui
# 또는
python run_gui.py
```
- 파일/폴더를 추가해 여러 자료를 한 번에 첨부
- Provider, Model, 언어, 토큰·탬퍼러처 설정 후 “생성 시작”
- API 키는 환경변수 또는 `.env`에 설정 필요

### 설치
- Python 3.10+
- 의존성 설치:
  - `pip install -r requirements.txt`
  - 필요 시 `.env.example`를 복사해 `.env` 작성

### 환경변수
- OpenAI
  - `OPENAI_API_KEY` (필수)
  - `OPENAI_MODEL` (선택, 기본: `gpt-4o-mini`)
  - `OPENAI_ORG_ID` (선택, 조직이 여러 개인 경우)
  - `OPENAI_PROJECT` (선택, 프로젝트 키/쿼터를 명시해야 할 때)
- Anthropic (Claude)
  - `ANTHROPIC_API_KEY` (필수)
  - `ANTHROPIC_MODEL` (선택, 기본: `claude-sonnet-4-5`)
    - **Claude 4.x 모델** (`-latest` 접미사 없이 자동 업데이트):
      - `claude-sonnet-4-5`: 최신 Claude 4.5 (권장)
      - `claude-haiku-4-5`: 빠르고 저렴한 모델
      - `claude-sonnet-4-5-20250929`: 특정 날짜 버전 고정
    - **Claude 3.x 모델** (`-latest` 접미사 사용):
      - `claude-3-7-sonnet-latest`: Claude 3.7
      - `claude-3-5-sonnet-20241022`: 이전 3.5 버전

### CLI 사용 예시
```bash
# 디렉토리 전체 + 개별 파일/패턴을 함께 첨부 가능
python -m src.main \
  --provider openai \
  --purpose "B2B 마케팅 블로그용: 데이터 기반 사례 중심, 실무 팁 강조" \
  --input-dir data/refs \
  notes/*.md slides/summary.txt \
  --out output/blog_draft.md

# Claude 사용 예시
python -m src.main \
  --provider anthropic \
  -p "초보 개발자 대상: 친절한 튜토리얼 톤" \
  -d 자료모음 \
  README.md \
  -o output/초안.md

# 또는 간단 실행
python run_cli.py --provider openai -p "목적" README.md
```

옵션
- `--provider` `openai|anthropic`
- `--model` 모델명(선택)
- `--purpose`/`-p` 글의 목적·타깃·톤 등 상세 지시
- `--input-dir`/`-d` 첨부 디렉토리(재귀)
- `files` 공백으로 구분한 파일 경로 또는 glob 패턴
- `--out`/`-o` 출력 파일 경로 (기본: `output/blog_draft.md`)
- `--lang` 출력 언어 (기본: `ko`)
- `--max-tokens` (기본: 1600)
- `--temperature` (기본: 0.7)

### 동작 방식
- 텍스트로 판별되는 파일만 읽어들입니다(`.txt,.md,.html,.json,.yaml` 등).
- 각 파일은 길이 제한에 맞춰 1개 청크만 사용합니다(토큰 초과 방지용).
- 첨부본은 프롬프트의 [첨부자료] 섹션에 파일명과 함께 포함됩니다.
- 출력은 Markdown으로 저장됩니다.

### 문제 해결
- 오류: `ImportError: attempted relative import with no known parent package`
  - 원인: 패키지 컨텍스트 없이 직접 파일을 실행했을 때 발생할 수 있습니다.
  - 해결: `python -m src.gui` 또는 `python run_gui.py`(GUI), `python -m src.main` 또는 `python run_cli.py`(CLI)로 실행하세요.
- API 호출이 끝없이 대기하는 경우
  - 네트워크/방화벽/프록시로 외부 API 접근이 차단되었을 수 있습니다.
  - 기본 타임아웃은 연결 15초, 읽기 120초입니다. 해당 시간이 지나면 오류로 표시됩니다.
  - 사내 프록시가 있다면 `HTTPS_PROXY`/`HTTP_PROXY` 환경변수를 설정하세요.
  - 커스텀 엔드포인트를 쓰면 `OPENAI_BASE_URL` 또는 `ANTHROPIC_BASE_URL`을 설정하세요.
  - 인증서 이슈가 있다면 `REQUESTS_CA_BUNDLE`로 사내 CA를 지정하세요.
  - GUI에서 “연결 테스트”로 빠르게 통신 가능 여부를 확인하세요 (모델 목록 API 호출).
  - GUI 로그에 단계별 메시지가 표시됩니다: 첨부 스캔 → 프롬프트 구성 → API 호출 → 완료.
- .env가 로드되지 않는 것 같다면
  - CLI에서 `--debug`로 실행: `python run_cli.py --provider openai -p test README.md --debug`
    - CWD, 프로젝트 루트, 로드된 .env 경로, API 키(마스킹)와 Base URL을 출력합니다.
  - GUI에서 “환경 점검” 버튼을 눌러 동일한 정보를 로그로 확인하세요.
  - .env는 프로젝트 루트와 현재 작업 디렉토리 모두에서 탐색/로드합니다. 루트의 `.env`를 우선 로드합니다.
- HTTP 429 (quota exceeded) 가 뜨는 경우
  - OpenAI 결제/크레딧 상태를 확인하거나 프로젝트 크레딧이 남은 곳으로 설정하세요.
  - 조직/프로젝트가 여러 개인 경우 `OPENAI_ORG_ID`, `OPENAI_PROJECT`를 설정해 올바른 쿼터를 사용하게 하세요.
  - 당장 진행이 필요하면 `--provider anthropic`으로 Claude 키로 생성 가능합니다.

### 주의 사항 / 확장 아이디어
- PDF, DOCX 등 바이너리는 기본 미지원입니다. 필요 시 추출기 추가(PDF: `pypdf`, DOCX: `python-docx`).
- 첨부가 매우 길면 추가 청크를 회차로 나눠 병합하는 멀티턴 전략을 도입할 수 있습니다.
- 목적/톤/독자 수준에 따른 템플릿 변형(예: 튜토리얼, 분석 보고서, 리뷰 등)도 쉽게 확장 가능합니다.
