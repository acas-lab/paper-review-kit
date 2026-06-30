# [공유] 논문 PDF → 6탭 학습용 HTML 변환 키트 (paper-review-kit)

논문 한 편을 **번역·해부·배경수식·비판질문·시뮬레이터·Q&A 6개 탭이 들어간 학습용 HTML 한 장**으로 만들어 주는 키트를 정리해서 공유합니다. 빌드 버튼 하나로 끝나는 도구가 아니라, **Claude Code와 대화하며 한 단계씩** 콘텐츠를 채워 마지막에 단일 HTML로 조립하는 방식입니다. 만들어진 HTML은 그림이 전부 안에 박혀 있어 **USB·메일로 옮겨도 그대로 열립니다.**

## 📦 저장소
https://github.com/acas-lab/paper-review-kit

## 🚀 사용법 — 두 가지 중 선택
- **웹앱 (비개발자 권장)** — Windows는 `webapp/win_start.bat` 더블클릭, Linux/macOS는 `webapp/linux_start.sh` 실행 → 브라우저에서 PDF 올리고 채팅으로 빌드. 각자 본인 Claude 구독으로 동작(별도 API 키 불필요).
- **CLI 대화형** — 폴더에서 `claude` 실행 후 대화하며 단계별 빌드. 흐름은 `SETUP.md` → `workflow.md` 참고.

## 🔧 준비물
1. **Claude Code** + Claude 계정/구독 (엔진 역할)
2. **Python 3.10 이상** — [python.org](https://python.org)에서 설치
   - *PyMuPDF 등 라이브러리는 자동 설치되니 따로 깔 필요 없습니다.* (웹앱은 런처가 venv에, CLI는 `tools/`가 첫 실행 때 스스로 설치 — Python 본체만 있으면 됨)
3. (선택) **codex CLI** — 학습 보조 이미지 생성용

## 📖 시작 방법
- 저장소를 받은 뒤 **`SETUP.md`부터** 읽으면 설치~첫 논문 빌드까지 단계별로 따라할 수 있습니다.
- 논문 PDF를 `rawpaper/` 폴더에 넣고, 폴더에서 Claude Code를 열어 시작 명령(README의 "시작 명령" 블록)을 붙여넣으면 됩니다.
- 잘 만든 기준 예시는 `samples/`(SAFE·FrameFusion·SGL)와 완성 워크드 예제 `samples/free_example/`에 있습니다.

---

⚠️ 동봉된 완성 HTML 속 **논문 그림·원문은 원저작자 저작권**(교육·예시 목적)이니, **재배포·상업적 이용은 삼가** 주세요. 자세한 건 `NOTICE.md` 확인 부탁드립니다.
