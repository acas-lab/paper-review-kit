# Paper Review 웹 대시보드 — 기획 (PLAN)

> 상태: **MVP 구현·검증 완료 (2026-06-22).** 사용법은 `webapp/README.md`.
> 작성일: 2026-06-19. 엔진 = **claude-agent-sdk**(Python)로 확정 (검증: `webapp/verify_glue.py`).
>
> **연구실 배포 결정(2026-06-22)**: 중앙 서버 ❌ → 각자 PC 로컬 실행. 엔진이 각자의
> Claude 구독(OAuth)이라 중앙화하면 계정 공유 문제 발생. 전원 유료 구독 보유 전제 →
> API 키·공용키 폴백 미사용(백로그). 타깃=비개발자 → `start.py` + OS별 원클릭 런처(`win_start.bat`/`linux_start.sh`)
> (전제조건 자동점검 + venv 자동생성 + 친절한 에러).
>
> **구현 현황**: backend(`main.py` FastAPI: auth·papers·upload·WS 채팅) + runner(`runner.py`
> ClaudeSDKClient 멀티턴, venv를 PATH 앞에 주입해 Claude의 Bash python도 자기완결) +
> frontend(채팅·업로드·목록·미리보기, v3 토큰) + 런처. 전 엔드포인트 200·WS 채팅 풀스택 검증.
> 남은 일(백로그) = §9 이후 항목 + 한 논문 실전 end-to-end 빌드.

---

## 0. 한 줄 요약

논문 PDF를 6탭 학습 HTML로 만드는 **대화형 작업**을, 터미널 대신 **브라우저 대시보드**에서 하게 한다.
백엔드는 **이미 로그인된 Claude Code를 그대로 호출**(OAuth 폴백)하므로, *Claude Code를 설치·로그인한 사람*이면 별도 API 키 없이 자기 구독으로 쓴다.

---

## 1. 목표 / 비목표

**목표**
- 학생이 터미널을 몰라도, 브라우저에서 ① Claude와 자연어 대화 ② PDF 업로드 ③ 진행 실시간 확인 ④ 완성 HTML 미리보기·다운로드를 할 수 있다.
- 기존 자산(CLAUDE.md·prompts·rules·samples·`_build.py`·PyMuPDF·codex 호출)을 **그대로 엔진으로 재사용**한다. 분석 로직을 새로 짜지 않는다.
- "이 번역 다시", "그림 잘렸어" 같은 **사람 교정 루프**를 채팅 UI에 그대로 보존한다 (품질의 핵심).

**비목표 (1차 범위 밖)**
- 인터넷에 배포되는 멀티유저 호스팅 서비스 (1차는 **로컬 단일 사용자** localhost 앱).
- 풀자동 "업로드→끝" 파이프라인 (대화형 유지가 의도).
- 계정 관리/로그인 화면 자체 구현 (인증은 Claude Code에 위임).

---

## 2. 인증 모델 (기본 결정)

- 백엔드는 `--bare`를 **쓰지 않는다**. 일반 모드여야 ① CLAUDE.md·rules 자동 로드 ② 로그인 OAuth 폴백이 동작.
- `ANTHROPIC_API_KEY`를 **설정하지 않는다.** 키가 없으면 Claude Code는 자동으로 *로그인된 구독 계정(OAuth)* 으로 폴백한다.
- 따라서 **이용 자격 = "이 PC에 Claude Code 설치 + `claude` 로그인 완료"**. 사용량은 그 사람의 구독(Pro/Max) 한도에서 차감된다.
- (선택) 더 안정적인 무인 운영이 필요하면 `claude setup-token`으로 구독 연동 1년 토큰을 발급해 환경변수로 둘 수 있다 — 1차에서는 미사용.

**주의**
- 구독 rate limit에 걸릴 수 있음(논문 1편 = 토큰 다수). UI에서 한도/오류를 친절히 표시.
- "각자 자기 계정"이 원칙. 한 계정을 여러 학생이 공유하는 형태는 지양(공정사용 위반 소지).

---

## 3. 아키텍처

```
┌────────────────────────────────────────────┐
│  브라우저 대시보드 (정적 HTML/JS, 빌드툴 무)   │
│  - 채팅 패널  - PDF 업로드  - 논문 목록        │
│  - 진행 로그(도구 사용 표시)  - HTML 미리보기   │
└───────────────┬────────────────────────────┘
                │  WebSocket (양방향 스트리밍) + REST(업로드/파일)
┌───────────────▼────────────────────────────┐
│  로컬 백엔드  (Python · FastAPI + uvicorn)    │
│  - 세션/대화 상태 관리                         │
│  - claude 서브프로세스 구동 & 스트림 파싱       │
│  - 파일 I/O (papers/N. name/ 생성, 결과 서빙)   │
└───────────────┬────────────────────────────┘
                │  subprocess: claude -p (stream-json)
┌───────────────▼────────────────────────────┐
│  Claude Code (로그인된 구독으로 실행)          │
│  cwd = 프로젝트 폴더 → CLAUDE.md/rules 자동로드 │
│  Bash 툴: PyMuPDF 크롭 · codex 이미지 · _build │
└─────────────────────────────────────────────┘
```

- **백엔드 언어 = Python** 권장: 기존 `_build.py`·`_crop.py`·PyMuPDF가 전부 Python이라 그대로 재활용.
- 프론트는 1차엔 의존성 없는 순수 HTML+JS(또는 가벼운 Vite). 빌드 복잡도 최소화.

---

## 4. 백엔드가 Claude를 부르는 방식 (핵심 글루)

서브프로세스 호출(개념):

```
claude -p \
  --output-format stream-json \
  --include-partial-messages \
  --verbose \
  --permission-mode acceptEdits \
  --allowedTools "Read,Write,Edit,Bash(python *),Bash(codex *),Bash(mkdir *),Bash(cp *),Glob,Grep" \
  --disallowedTools "Bash(rm *),Bash(sudo *),Bash(curl *),Bash(git push *)"
  # cwd = 프로젝트 폴더, --bare 미사용, ANTHROPIC_API_KEY 미설정
```

- stdin으로 사용자 메시지를 흘려보내고(stream 입력), stdout의 **줄 단위 JSON 이벤트**를 파싱.
- 이벤트 → 브라우저 매핑:
  - `content_block_delta / text_delta` → 채팅에 글자 스트리밍
  - `content_block_start (tool_use)` → "🔧 Bash 실행 중… / 그림 생성 중…" 배지
  - `content_block_stop` → 도구 완료 표시
  - `result` (최종) → 토큰/비용/세션ID 표시, 결과 HTML 경로 노출
- 멀티턴 대화는 `--resume <session_id>`로 같은 세션 이어가기.

**권한 설계**: `acceptEdits`(파일 편집 자동 승인) + 화이트리스트 Bash 패턴만 허용, 파괴적 명령(`rm`,`sudo`,`git push`)은 명시적 차단. `bypassPermissions`는 쓰지 않는다(안전).

---

## 5. 학생 사용 흐름 (UX)

1. 대시보드 접속(localhost) → 상단에 인증 상태 표시("Claude 로그인됨: ○○" / 미로그인 시 안내).
2. **PDF 업로드** → 백엔드가 `rawpaper/`에 저장하고 `papers/N. shortname/` 골격 생성. 폴더명 규약(`N. shortname`) 자동 제안.
3. 채팅에 자연어로: *"이 논문 workflow.md 10단계로 6탭 HTML 만들어줘. 디자인은 SGL 정본, ⑤⑥은 셸만."*
4. 진행이 실시간 로그로 흐름(텍스트 + 도구 배지). 중간에 "그림 다시", "이 번역 어색해" 교정 가능.
5. 완성되면 **미리보기 iframe** + **다운로드 버튼**. 결과는 self-contained HTML 한 장.

---

## 6. 디렉토리 (구현 시 예정)

```
webapp/
├── PLAN.md            ← (이 문서)
├── backend/
│   ├── main.py        · FastAPI 엔트리 (REST + WebSocket)
│   ├── claude_runner.py · claude -p 서브프로세스 구동 + stream-json 파싱
│   ├── papers.py      · 업로드/폴더 생성/결과 서빙
│   └── requirements.txt
├── frontend/
│   ├── index.html     · 대시보드
│   ├── app.js         · WebSocket 채팅 + 업로드 + 미리보기
│   └── style.css      · v3 디자인 토큰 재사용
└── start.py           · 의존성 체크 → 서버 기동 → 브라우저 오픈
```

> 최종적으로 이 `webapp/`는 **public 키트(paper-review-kit)** 에도 포함시켜 배포한다.

---

## 7. 이미지 생성 — 모드 선택 (codex PNG / Claude SVG)

- **두 모드 선택 (2026-06-29 추가)**: 상단 토글로 사용자가 고른다.
  - **모드 A `codex`** — 백엔드 Claude가 **CLAUDE.md §11 "6계명"** 대로 Bash로 `codex`를 직접 호출 → PNG. 규칙: 플러그인 없이 직접 터미널 제어 / prompt.txt UTF-8 / `< /dev/null` / **이미지 내부에 논문 제목·헤더·저자명 금지** / 출력 경로·해상도 명시. 전제: `codex` CLI 설치·로그인.
  - **모드 B `claude_svg`** — Claude가 외부 도구 없이 **인라인 `<svg>` 도식을 직접 작성**. codex 불필요. v3 토큰으로 테마 일관. codex 미설치 시 자동 폴백.
- 프론트가 매 메시지에 `[이미지 생성 모드: codex|claude_svg]` 태그를 붙이고, 백엔드 `runner.WEBAPP_APPEND`가 그 태그의 의미를 세션에 주입한다. 규약 정본: `rules/component_rules.md` §11.8 (CLI·웹 공통).
- codex 미설치면 토글이 `claude_svg`로 잠겨 그래도 이미지 단계가 진행된다(graceful degrade).

---

## 8. 전제 조건 / 셋업 (학생 PC)

1. **Claude Code 설치 + `claude` 로그인** ← 이용 자격
2. **Python 3.10+** + `pip install -r webapp/backend/requirements.txt` (fastapi, uvicorn, pymupdf 등)
3. (선택) **codex CLI** 설치·로그인 — 학습 보조 이미지용
4. 실행: `python webapp/start.py` → 브라우저 자동 오픈 → 채팅 시작
   - (API 키 설정 단계 없음)

---

## 9. MVP 범위 vs 이후

**MVP (1차)**
- WebSocket 채팅(스트리밍) + PDF 업로드 + 진행 로그 + 결과 미리보기/다운로드
- 단일 논문, 단일 사용자, localhost
- 권한 화이트리스트 + 인증 상태 표시

**이후 (백로그)**
- 논문 목록/재방문, 세션 저장·복원
- 단계별 진행 표시(① ~ ⑥ 탭 상태 배지)
- codex 이미지 갤러리/재생성 버튼
- 멀티유저·호스팅(인증·격리·과금 고려), Docker 패키징
- 풀자동 모드(검수 최소) 옵션

---

## 10. 리스크 / 오픈 이슈

- **rate limit**: 긴 논문은 구독 한도 소진 가능 → 진행 분할/재개(resume) 필요할 수 있음.
- **장시간 실행**: 빌드가 수 분~수십 분. WebSocket 끊김 대비 재연결 + 세션 resume.
- **OAuth 폴백 보장**: 일반 모드 + 키 미설정 전제. 머신에 다른 곳에서 들어온 `ANTHROPIC_API_KEY`가 환경에 남아 있으면 그게 우선되니, 시작 스크립트에서 점검/경고.
- **codex 미설치 환경**: 이미지 단계 스킵 경로 명확히.
- **경로 공백·한글**: `papers/N. shortname` 경로에 공백/마침표 → 모든 경로 따옴표 처리(기존 규칙과 동일).
- **보안**: localhost 바인딩 고정, 파괴적 Bash 차단, 업로드 파일 검증(PDF만).

---

## 11. 다음 액션 (합의 후)

1. 이 PLAN 리뷰·수정 → 확정
2. `webapp/backend/claude_runner.py` 프로토타입: `claude -p` 스트림 파싱 1개 검증(가장 불확실한 부분 먼저)
3. 최소 프론트(채팅+업로드) 연결
4. 한 논문으로 end-to-end 스모크 테스트
```
