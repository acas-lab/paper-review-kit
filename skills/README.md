# skills/ — 킷이 함께 배포하는 Claude Code 스킬

| 스킬 | 쓰는 곳 | 출처·라이선스 |
|---|---|---|
| `motion-broll/` | 논문 소개 영상(Stage 13)의 motion 클립 엔진과 클립 작성 규칙(`reference/engine-api.md`) | 공개 스킬 저장소 `Barty-Bart/motion-graphics`의 motion-broll, MIT (`motion-broll/README.md` "Licence", 글꼴 Geist는 OFL) |

**설치:** 이 폴더는 배포본(원본)이다. 쓰는 위치는 프로젝트 스킬 폴더 `.claude/skills/motion-broll/`이고, 없으면 `python tools/video/make_video.py - doctor`(또는 `- setup`, 클립 단계)가 이 폴더를 그대로 복사해 설치한다. Windows는 `setup/8_install_video.bat`도 같은 일을 한다. `.claude/`는 git에서 제외된다.

**고칠 때:** `.claude/skills/motion-broll/`이 아니라 이 폴더를 고치고 `python tools/video/make_video.py - setup`으로 다시 복사한다(`doctor`는 두 곳이 다르면 "배포본과 다름"으로 알린다).

`motion-broll/README.md`의 데모 GIF 링크(`../../docs/…`)는 원 저장소 기준이라 이 킷에는 없다.
