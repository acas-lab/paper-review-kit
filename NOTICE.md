# NOTICE — 저작권 및 이용 범위

이 저장소는 **학습용 방법론 키트**입니다. 두 종류의 내용이 섞여 있으니 구분해서 이해해 주세요.

---

## 1. 키트 저작자의 결과물 (자유 학습 이용 OK)

다음은 이 키트를 만든 사람이 직접 작성한 것으로, 학습·교육 목적으로 자유롭게 사용·수정할 수 있습니다.

- `CLAUDE.md`, `workflow.md`, `README.md`, `SETUP.md`, `GUIDE.html`
- `prompts/`, `rules/` (작업 규칙·프롬프트)
- `tools/`(영상 파이프라인 `tools/video/`의 코드 포함), `templates/paper_base/`(기준 빌더·영상 뼈대) 및 각 예시의 `_build.py` 등 빌드 스크립트
- `webapp/`(로컬 웹 대시보드), `setup/`(Windows 설치·실행 스크립트)
- 산출 HTML의 디자인·레이아웃·인터랙션 코드(CSS/JS), 학습 해설·번역 등 **2차적 저작 부분**

다만 위 2차적 저작물(번역·해설)은 아래 원논문에 근거한 파생물이므로, 무단 재배포보다는 **개인/수업 내 학습 용도**로 사용해 주세요.

---

## 2. 원논문에서 가져온 부분 (원저작자 저작권 — 재배포 금지)

`samples/`와 `papers/`의 완성 HTML에는 학습 맥락을 위해 다음이 포함되어 있습니다.

- 원논문의 **Figure / Table 이미지** (base64로 내장)
- 원논문의 **원문 텍스트** (① 원문/번역 탭)

이 부분의 저작권은 **각 논문의 저자 및 출판사**에 있습니다. 여기서는 *교육·예시* 목적으로 제한적으로 포함했을 뿐이며, 다음을 지켜 주세요.

- ❌ 이 그림·원문을 떼어내 재배포하거나 상업적으로 이용하지 마세요.
- ❌ 완성 HTML 자체를 공개 재배포하지 마세요 (개인 학습·수업 내 공유까지가 안전한 범위).
- ✅ 자기 논문을 빌드할 때는, 본인이 **적법하게 입수한 PDF**로 진행하세요.

포함된 견본/예시 논문:
- `samples/cares/` — CARES: Context-Aware Resolution Selector for VLMs (ACL 2026)

---

## 3. 함께 배포하는 제3자 자료 (각 라이선스를 따릅니다)

논문 소개 영상(Stage 13) 파이프라인이 쓰는 자료입니다. 위 1절의 "키트 저작자의 결과물"과 라이선스가 다릅니다.

| 자료 | 위치 | 출처·라이선스 |
|---|---|---|
| motion-broll 스킬 (클립 엔진·작성 규칙·예시 클립) | `skills/motion-broll/` (설치하면 `.claude/skills/motion-broll/`) | 공개 스킬 저장소 `Barty-Bart/motion-graphics`의 motion-broll. **MIT** (`skills/motion-broll/README.md` "Licence"). 아이콘 경로는 Lucide(ISC)에서 변형 |
| Geist · Geist Mono 글꼴 | `skills/motion-broll/engine/fonts/` | Vercel · basement.studio, **SIL Open Font License 1.1** (`OFL-Geist.txt`) |
| Noto Sans KR 글꼴 (가변 판 + 자막용 700 고정 판 `NotoSansKR-Sub700.ttf`) | `tools/video/fonts/` | Adobe (Google Noto CJK 계열), **SIL Open Font License 1.1** (`tools/video/OFL-NotoSansKR.txt`). Sub700은 700 굵기로 고정한 파생 판이며 이름을 "Noto Sans KR Sub"로 바꿨다(OFL 예약 이름 규정) |
| 목소리 원본 7개 | `tools/video/voices/*.mp3` | 실존 인물의 목소리가 아닌 합성 화자 샘플이며, 키트 저작자가 사용 권한을 확보했다. TTS(Qwen3-TTS)의 화자 기준 음원으로만 쓴다. 파일 이름은 측정한 음성 특징(성별·음역·빠르기·밝기)이다(`rules/video_rules.md` 6절). 음원을 떼어내 다른 목적으로 재배포하지 않는다 |

TTS 모델(Qwen3-TTS 0.6B)·faster-whisper 모델·torch·Chromium·ffmpeg는 저장소에 들어 있지 않고, 처음 실행할 때 각 배포처에서 내려받는다(각 라이선스를 따른다).

## 4. 원논문 PDF는 포함하지 않습니다

저작권상 원논문 PDF 원본(`rawpaper/`)은 이 저장소에 포함하지 않았습니다.
논문 PDF는 각자 출판사/arXiv 등 **적법한 경로로 직접 입수**하세요.

같은 이유로 `.gitignore`가 `rawpaper/`의 PDF와 `papers/` 아래 각자 빌드한 논문 폴더를 기본으로 제외합니다.

## 5. 이 배포본에 들어 있지 않은 것

- 논문 콘텐츠는 `samples/cares/` 한 편뿐입니다. 문서가 "모체 사례 — 배포본 미포함"으로 언급하는 다른 논문(`papers N` 표기)과 1~3세대 견본 HTML(SAFE·FrameFusion·SGL)은 들어 있지 않습니다.
- 완성된 소개 영상 예제(`*_video.mp4`)와 그 원고는 들어 있지 않습니다. 새 논문은 `templates/paper_base/video/` 뼈대에서 시작합니다. 렌더 결과(`video/work/`, `*_video.mp4`)는 `.gitignore`가 제외합니다.

---

문의나 권리 관련 요청이 있으면 저장소 소유자에게 알려 주세요. 정당한 요청에는 해당 자료를 신속히 내리겠습니다.
