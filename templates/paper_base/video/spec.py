# -*- coding: utf-8 -*-
"""{{PAPER}} 영상 명세. tools/video/가 읽는다 (rules/video_rules.md 4절). 이 파일이 시작 뼈대다

논문마다 달라지는 값만 둔다: 애니매틱 페이지 문구, 장 곡선, 자막 표기, TTS 읽기, 인용 위치, 출처 자막, 장면 이미지.
"""

# ------------------------------------------------------------- 애니매틱 페이지(video/기획안.html) 문구
PAGE = {
    "title": "{{SHORT}} 다큐멘터리 애니매틱",
    "eyebrow": "기획안 v1 · TODO_PAPER 날짜 · {{PAPER}}",
    "h1": "TODO_PAPER 영상 제목",
    "lead": "TODO_PAPER 이 영상이 무엇을 어떤 흐름으로 보여 주는지 두세 문장. 재생하면 원고 속도로 컷이 넘어가고 자막이 나옵니다(소리 없음).",
    "notes_html": """    <div><h4>화면 문법</h4><ul>
      <li>도형으로 설명하는 장면은 motion 클립, 실제 자료(사진·PDF 지면·원문 그림)는 캔버스 장면으로 보여 줍니다.</li></ul></div>
    <div><h4>사실 경계</h4><ul>
      <li>저자의 고민은 논문 서론·관찰 문장으로만 말하고, 일화와 감정은 만들지 않습니다.</li></ul></div>
    <div><h4>소리</h4><ul>
      <li>내레이터는 여성, 저자 인용은 남성 원본 음원 1개씩(<code>tools/video/voices/</code>, 혼합 없이).</li></ul></div>""",
}

# 장 라벨 → (곡선 색 종류 hook|problem|clue|turn|solve|result, 곡선 높이 0~1): 시청자가 붙잡은 질문의 무게
ARC = {
    "프롤로그": ("hook", .45), "1장": ("problem", .7), "2장": ("clue", .55), "3장": ("problem", .8), "4장": ("turn", .6),
    "5장": ("turn", .7), "6장": ("solve", .35), "7장": ("result", .45), "8장": ("problem", .65), "에필로그": ("hook", .22),
}
LOGLINE = {"프롤로그": "TODO_PAPER 장 한 줄 요약"}

# ------------------------------------------------------------- TTS 읽기 (원고에 영문이 남았을 때의 안전망, 긴 것부터)
READ_WORDS = []

# ------------------------------------------------------------- 자막 표기: 원고의 한국어 읽기 → 화면 영문 표기 (긴 것부터)
NAMES = [
    # 예(AI/CS): ("엘라바 일점오 칠비", "LLaVA-1.5-7B"), ("텍스트브이큐에이", "TextVQA"), ("그림 5", "Figure 5"), ("표 1", "Table 1"),
]
# 장마다 첫 등장만 "English(한국어)"
# 아래는 AI/CS 논문 예시다. 논문 분야의 용어로 바꾼다(config.json#domain.term_style)
TERMS = [("어텐션", "Attention"), ("토큰", "Token"), ("벤치마크", "Benchmark"), ("처리량", "Throughput"), ("어블레이션", "Ablation")]

# ------------------------------------------------------------- 인용 컷의 PDF 형광펜 위치
# 비워 두면 인용 컷 출처 sentence_id의 영어 원문을 PDF에서 자동으로 찾는다. 못 찾은 것만 적는다:
# "sentence_id": (0부터 센 쪽, [(x0, y0, x1, y1) pt, …])
QUOTES = {}

# ------------------------------------------------------------- 외부 자료 출처 자막: (문구, 시작 컷, 끝 컷). CREDITS.md와 같이 고친다
CREDITS = []

# ------------------------------------------------------------- 장면 이미지 (scenes.js의 img.키)
def images(x):
    """x: b64(im, fmt, q), crop(asset_id, box200dpi) 400 DPI 재렌더, embedded(xref) PDF 내장 원본, Image(PIL), video_dir, paper_dir.
    기본: 논문 assets/의 그림·표 PNG 전부(키 = 자산 id). 사진 장면은 embedded(xref)나 video/assets/의 원본을 쓴다."""
    out = {}
    for p in sorted((x.paper_dir / "assets").glob("*.png")):
        out[p.stem] = x.b64(x.Image.open(p).convert("RGB"), q=90)
    return out
