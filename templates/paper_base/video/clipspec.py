# -*- coding: utf-8 -*-
"""{{PAPER}} motion-broll 클립 명세. `make_video.py briefs`가 타임라인과 단어 시각을 붙여 work/briefs/NN-name.md를 만든다.
규칙: rules/video_rules.md 7·8절. 클립 조각 작성법: .claude/skills/motion-broll/reference/engine-api.md (배포본 skills/motion-broll/)

- 도형으로 설명하는 장면(원리·흐름·비교·식·수치)은 모두 클립으로 만든다. 실제 자료(사진·PDF 지면·원문 그림)는 scenes.js.
- 사진이 들어가는 클립은 spec에 이미지 파일(assets/…)·"예시 사진" 표기·이미지 위 상자 좌표(원본 픽셀)를 적는다.
  사진 자리를 도형으로 지시하지 않는다("실제 사진 아님"·"추상 장면" 금지). 이미지는 논문 자료 → codex 예시 사진 → 데이터셋 순서(2절).
- cuts = 이 클립이 덮는 연속 컷. 클립끼리 겹치지 않는다.
- spec = 무엇을 어떤 단어에 보여 주나 + 화면에 쓸 논문 수치(조건 포함). 예시 값이면 "예시"라고 적는다.
STYLE을 두지 않으면 tools/video/motion.py의 DEFAULT_STYLE(밝은 팔레트, 하단 25% 자막 자리)을 쓴다.
"""

CLIPS = [
 # dict(id="01", name="two-ways", cuts=["c08", "c09"], spec="""\
 # 필요한 곳을 찾는 두 방법의 좌우 비교. pill "필요한 곳은 누가 찾나" → 좌우 비교 카드. …"""),
]
