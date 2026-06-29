# Paper Review HTML Kit

논문 PDF 한 편을 **6탭 학습용 HTML 한 장**으로 바꾸는 작업 키트입니다.
빌드 스크립트로 한 방에 돌리는 도구가 아니라, **Claude Code와 대화하며 한 단계씩** 콘텐츠를 만들고 마지막에 단일 HTML로 조립하는 *방법론 + 정본 템플릿 + 보조 도구* 묶음입니다.

> 이 방식이 괜찮다고 판단해 주신 지도교수님의 권유로, 같은 방법을 다른 학생들도 자기 컴퓨터에서 쓸 수 있게 정리한 배포본입니다.

---

## 무엇이 만들어지나

논문 한 편당 아래 6개 탭을 가진 **self-contained HTML 한 장**(모든 그림이 base64로 박혀 USB·메일로 옮겨도 그대로 열림):

| 탭 | 내용 |
|---|---|
| ① 원문 / 번역 | 영한 문장 단위 호버 동기화 + 자산 해석 + 초보자 해설 |
| ② Paper Dissection | 동기·관찰·차별점·방법·검증·한계 + 총정리 카드 |
| ③ Background & 핵심 수식 | 배경지식 + 주요 수식 풀이 |
| ④ Questions & Diagrams | 비판적 질문 + 직관 도식 |
| ⑤ Simulator & Code | 핵심 알고리즘 시뮬레이터 (기본은 셸만) |
| ⑥ 학습 기초 Q&A | 자가 점검 (기본은 셸만) |

⑤·⑥은 기본 빌드에서 셸(탭 골격)만 만들고, 더 깊이 파고들고 싶을 때만 따로 채웁니다.

---

## 두 가지 사용법

- **🌐 웹앱 (비개발자 권장)** — `webapp/start.bat` 더블클릭 → 브라우저에서 PDF 올리고 채팅으로 빌드. 각자 본인 Claude 구독으로 동작(별도 API 키 없음). 준비물·사용법: **`webapp/README.md`**.
- **⌨️ CLI 대화형** — 터미널에서 Claude Code를 열고 이 폴더에서 대화하며 단계별로 빌드. 흐름: **`SETUP.md`** → `workflow.md`.

전제: 두 방식 모두 **Claude Code 설치 + 로그인**이 필요합니다.

---

## 키트 구성

```
paper-review-kit/
├── README.md              ← 지금 이 문서
├── SETUP.md               ← ★ 설치 + 첫 논문 따라하기 (여기부터 읽으세요)
├── NOTICE.md              ← 저작권·이용 범위 고지 (꼭 확인)
├── CLAUDE.md              ← 작업 규칙 정본 (Claude Code가 자동으로 읽음)
├── workflow.md            ← 10단계 작업 흐름
├── prompts/               ← 단계별 프롬프트 (01_cleaning … 10_qa)
├── rules/                 ← 파싱/분석/코칭/지식/수식/컴포넌트 규약
├── tools/                 ← 재사용 도구 (PDF 크롭·캡션 좌표 검출·재파싱)
├── webapp/                ← 브라우저 대시보드 (비개발자용 — start.bat 더블클릭)
├── samples/               ← 정본 견본 + 워크드 예제 (디자인·인터랙션 기준 — 베껴 시작)
│   ├── SAFE.html         (1세대)
│   ├── FrameFusion.html  (2세대)
│   ├── SGL.html          (3세대 — 신규 논문은 이걸 베이스로)
│   └── free_example/            (완성 워크드 예제: 입력 JSON → 단일 HTML 전 과정)
└── papers/                ← 비어 있음. 새 논문을 빌드하면 "1. shortname"부터 순차로 쌓임
```
> 완성 워크드 예제(입력 JSON → 단일 HTML 전 과정)는 `samples/free_example/`에 있습니다.

`samples/`의 3편이 **"잘 만든 기준"**입니다. 신규 논문은 이 마크업·CSS·인터랙션을 베껴 시작합니다.
`samples/free_example/`는 *데이터(JSON) → 단일 HTML* 조립이 실제로 어떻게 되는지 보여주는 완성 예시입니다.

> 참고: `CLAUDE.md`/`rules/`는 다른 사례 논문(예: `papers/4. perceptron`, `20. sparse_vlm`, `24. geollava8k`)도 언급하는데, 이 배포본에는 위 견본·예시만 포함됩니다. 나머지는 방법을 이해하는 데 필수가 아닙니다.

---

## 시작하기

👉 **[SETUP.md](SETUP.md)** 를 먼저 읽으세요 — 필요한 프로그램 설치부터 첫 논문 빌드까지 단계별로 안내합니다.

핵심만 요약하면:

1. **Claude Code** + Claude 계정/구독 (엔진)
2. **Python 3 + PyMuPDF** (`pip install pymupdf`) — PDF 텍스트/그림 추출용
3. (선택) **codex CLI** — 학습 보조 이미지 생성용
4. 이 폴더에서 `claude` 실행 → 자기 논문 PDF를 주고 *"workflow.md 10단계로 6탭 HTML 만들어줘"* 라고 대화 시작

---

## 라이선스 / 이용 범위

**[NOTICE.md](NOTICE.md)** 를 반드시 확인하세요. 요약: 키트의 *방법론·프롬프트·규칙·도구·문서*는 자유롭게 학습용으로 쓰되, `samples/`·`papers/`의 완성 HTML에 박힌 **논문 그림·원문은 원저작자 저작권**이며 교육·예시 목적 동봉입니다. **재배포·상업적 이용은 하지 마세요.**
