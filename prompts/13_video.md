# Stage 13 — 논문 소개 영상 (기본 빌드 포함)

규칙 정본은 `rules/video_rules.md`다. 이 프롬프트는 한 논문의 영상을 만들 때 Claude가 따르는 작업 순서다. 시작 뼈대는 `templates/paper_base/video/`(`make_video.py … new`가 복사)이고, 완성된 영상 예제는 배포본에 없다(모체 사례 — 배포본 미포함). 분야는 묻지 않는다 — 같은 구조에 그 논문 분야의 사례·증거를 넣는다(`config.json#domain`).

## 0. 시작 전

- HTML 빌드(Stage 0~11)가 끝나 있어야 한다. 영상 원고의 재료는 `tabs_data/dissection.json`(카드 8장), `study.json`(phase1~3), `knowledge.json#equations`, `analysis.json#study_modals`, `translations/manual.json`, `assets/`다.
- **motion-broll 스킬:** `.claude/skills/motion-broll/SKILL.md`가 없으면 `skills/motion-broll/`을 `.claude/skills/motion-broll/`로 복사해 설치한다(`make_video.py - doctor`가 자동으로 한다).
- `python tools/video/make_video.py "papers/N. name" new` → `video/` 뼈대. 새 컴퓨터면 `python tools/video/make_video.py - doctor`로 점검하고 빠진 것을 `- setup` · `- setup-tts`로 채운다(`rules/video_rules.md` 13절).

## 1. 원고 설계 (대화 세션에서 Claude가 쓴다)

1. `기획안.md`의 `## 0. 기획` 표를 먼저 채운다: 주인공 예시, 출발 문제, 방법 한 문장과 단계, 핵심 식 1개, 가장 가까운 기존 방법·차이·대가, 대표 수치 2개(조건 포함), 한계, HTML 길잡이 3곳.
   - 입력 이미지가 나오는 컷을 이 단계에서 모두 찾고, 컷마다 화면 이미지를 **① 논문 자료(정성 사례 그림·원문 크롭) → ② codex 예시 사진 → ③ 벤치마크·샘플 데이터셋** 순서로 정한다. ②는 사진 프롬프트를 `video/assets/prompt_*.txt`로 쓰고 `check-assets`를 통과시킨 뒤 codex를 부른다(`rules/video_rules.md` 2절). 고른 이미지는 `video/assets/sources.json`에 출처 종류와 함께 적는다. 사진 자리를 도형으로 그리지 않는다.
2. 장을 나눈다(`rules/video_rules.md` 3절 표). 본 장 6~9개, 장 제목은 짧은 명사구.
3. 컷을 쓴다. 한 컷 = 1~3문장, 한 가지 생각. 내레이터는 3인칭, 저자 인용은 번역본 문장 그대로(핵심 절만 읽어도 된다).
4. 출처 칸에 sentence_id·자산 id를 단다. 풀이 컷은 `설명`, 비유 컷은 `비유`.
5. 학부생 눈높이 규칙 7개(5절)를 지킨다. 특히 컷당 숫자 2개 이하, 식 1개, 용어 첫 등장 풀이, 방법 전체 그림을 세부보다 먼저.
6. 영문·숫자는 TTS 읽기로 적고, 그 읽기를 화면 표기로 되돌리는 쌍을 `spec.NAMES`에, 전문용어를 `spec.TERMS`에 넣는다.
7. `## 3. 사실 검토가 필요한 항목`에 계산한 값·해석한 문장의 근거를 적는다.
8. `check-script` → FAIL 0. 원고 추정 길이가 10~15분 밖이면 3절의 자르기·더하기 순서로 고친다.
9. 사실 검토: 원고만 받은 별도 서브에이전트가 수치·표현을 표 PNG와 원문에 대조하고(과장·근거 없는 단정 찾기), 고친 내용을 `## 3.`에 남긴다.
10. **원고 승인을 기다리지 않고 영상까지 끝까지 만든다**(기본). 사용자가 원고를 먼저 보겠다고 한 경우만 여기서 멈춘다. 완성 뒤 보고에 원고 경로를 적고, 고칠 문장이 오면 그 컷만 `tts`부터 다시 한다(음성은 캐시된다).

## 2. 음성과 애니매틱

- `tts` (Qwen3-TTS, 캐시되므로 고친 문장만 다시 생성). 실제 길이가 10:00~15:00인지 본다.
- `scenes.js`에 실제 자료 장면을 쓴다: 주인공 사진(고해상도 원본, `spec.images()`), 원문 Figure·Table 카메라 이동, 해상도 변화. 인용 컷은 비워 두면 PDF 형광펜 장면이 자동으로 붙는다.
- `animatic` → `video/기획안.html`을 브라우저로 열어 전체 흐름을 확인한다.

## 3. motion 클립

- 도형으로 설명하는 장면(원리·흐름·비교·식·수치)은 모두 클립이다. `clipspec.py`에 클립을 정한다(덮는 컷, 단어별 상태 변화, 쓸 수치).
- 사진이 들어가는 클립은 명세에 쓸 이미지 파일(`assets/…`)과 "예시 사진" 표기 여부, 이미지 위 상자·좌표(원본 픽셀 기준)를 적는다. "실제 사진 아님"·"추상 장면"처럼 사진 자리를 도형으로 지시하지 않는다.
- `words` → `briefs`. 클립 조각 작성은 서브에이전트에 브리프 단위로 맡길 수 있다. 전달: 브리프 경로, `.claude/skills/motion-broll/reference/engine-api.md`, 스킬 예시 `.claude/skills/motion-broll/examples/opus-aoe2/`, "조각 작성·`clips-build`·`beats` 점검까지만, 렌더 금지".
- 리드가 `beats` 시트를 직접 보고 `check-assets` FAIL 0을 확인한 뒤, `clips-render`를 포그라운드로 반복 실행한다.

## 4. 합성과 검사

- `base-render`(반복) → `final` → `check` FAIL 0(G11·G12 예시 이미지 포함) → `gapcheck` 시트를 직접 본다.
- 결과를 사용자에게 보고한다: 파일 경로, 길이, QC 결과(WARN 판단 포함), 직접 보지 못한 구간.
- 사용자 피드백으로 고칠 때는 원인을 도구(`tools/video/`)나 규칙(`rules/video_rules.md`)에서 고쳐 다음 논문에도 적용되게 한다. 이 논문에만 해당하는 것은 `video/` 안에서 고친다.
