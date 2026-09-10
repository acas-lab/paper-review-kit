# -*- coding: utf-8 -*-
"""qa_bridge.py - 메모 플로팅의 'Q&A 생성' 버튼을 위한 로컬 다리(bridge) 서버.

브라우저에서 열린 학습 HTML은 보안 샌드박스 때문에 직접 `claude`/`codex` CLI를
실행할 수 없다. 이 서버를 한 번 띄워두면(`python tools/qa_bridge.py`), 메모
드로어의 'Q&A 생성' 버튼이 localhost 로 요청 → 서버가 헤드리스 `claude -p` 를
spawn 해서 기존 Q&A 지침(prompts/10_qa.md)대로 qa.json 을 만들고 ⑥ tab-qa 에
주입한다. 필요하면 헤드리스 claude 가 Bash 로 codex 이미지도 생성한다.

핵심 설계
---------
- **증분 생성**: study/.qa_state.json 에 (a) 마지막 생성 시점 메모의 sha256,
  (b) 이미 생성한 질문 원문 목록을 기록. 요청 메모의 해시가 같으면 즉시
  `nochange` 반환(헤드리스 claude 미실행 = 중복·비용 차단). 다르면 이미 생성한
  질문 목록을 헤드리스 claude 에 넘겨 "새 질문만 append" 하도록 지시(의미 수준 dedup).
- **군집화·상한 없음 (v1.2, 2026-09-10)**: 이전 프롬프트는 "한 번에 최대 6개"로 카드 수를
  제한했다. 그런데 성공하면 메모 **전체** 해시가 processed_hash 로 봉인되므로, 상한에 걸려
  미뤄진 질문은 사용자가 메모를 고치지 않는 한 영구히 생성되지 않았다(papers 26·30 이 정확히
  6개에서 멈춰 있었다). 그래서 **상한을 없애고**, 대신 관련 있는 메모 항목들을 한 카드로
  **묶어 연결된 설명**으로 답하게 한다. 카드 수는 상한이 아니라 메모의 주제 수가 결정한다.
- **해시 봉인 규칙 (v1.2)**: 영구 차단 경로를 남기지 않는 것이 요구사항이다.
  · `ok` + `deferred == 0` → processed_hash 갱신(완료).
  · `ok` + `deferred > 0`  → **갱신하지 않음** - 같은 메모로 다시 눌러 나머지를 이어받는다.
  · `noop`                 → processed_hash 대신 **noop_hash** 에만 기록. 게이트는 둘 중
    하나라도 맞으면 nochange 를 돌려주되 `reason` 을 구분해, noop 쪽은 클라이언트가
    "새 질문이 없다고 판정된 메모입니다 - [그래도 다시 생성]" 으로 우회를 노출한다.
- **장부 단위 = 메모 항목**: QA_RESULT 에 `new_cards[{qid,title,covers[]}]` 를 받아
  covers 를 평탄화한 것을 generated_questions 에 누적한다(카드 단위로 기록하면 어떤 메모
  항목이 소화됐는지 잃어 다음 실행의 중복 판정이 부정확해진다). `new_questions` 는 하위 호환.
- **자동 JSON 저장**: 생성 직전 메모를 study/{Short}_study_notes_YYMMDD.json 으로
  저장(Stage 9 = prompts/10_qa.md 가 읽는 형식) - 요청 2번.
- **내용 무손실**: 서버는 메모를 읽기만 한다. textarea/localStorage 는 건드리지 않음.
- **우아한 실패**: 서버가 꺼져 있으면 버튼이 fetch 실패를 잡아 안내(클라이언트 쪽).

비동기 job (v1.1, 2026-09-10)
---------------------------
헤드리스 claude 는 10분을 넘기는 일이 흔한데, 브라우저 fetch 는 그만큼 못 기다린다
(AbortController 타임아웃·유휴 연결 정리·탭 이동). 실제로 10분 51초 걸린 작업이
서버에서는 **성공**했는데 클라이언트에는 "중단됨"으로 보이고, 응답을 쓰는 순간
`ConnectionAbortedError` 트레이스백이 콘솔에 찍혔다. 그래서 **접수와 조회를 분리**한다.

- `{"async":1}` 이 오면 job 을 백그라운드 스레드로 띄우고 즉시 202 + job_id 반환.
- 클라이언트는 `GET /job?id=` 를 폴링. job_id 는 localStorage 에 남아 새로고침해도 재접속.
- 같은 short 에 대해 job 이 이미 running 이면 **새로 만들지 않고 그 job_id 를 돌려준다**
  (새로고침 후 버튼 재클릭으로 claude 가 두 번 도는 것을 차단).
- `async` 가 없으면 예전처럼 **동기 응답** - 구버전 HTML 무손상(하위 호환).
- 끊긴 연결(ConnectionAborted/Reset/BrokenPipe)은 트레이스백 대신 한 줄 로그만 남긴다.

엔드포인트
---------
- GET  /ping        → {ok, version, papers}      (버튼이 서버 가동 여부 탐지)
- POST /gen-qa      {short, memo, force?, async?} → 증분 Q&A 생성
- POST /review-study {short, answers, async?}     → Paper Study 답변 검토
- GET  /job?id=<id> → {status:"running", elapsed, log_tail} | 완료된 결과 그대로
- OPTIONS *         → CORS preflight (혹시 대비)

CORS: file:// 페이지의 Origin 은 "null" 이므로 모든 응답에 ACAO:* 를 붙인다.

사용법
------
    python tools/qa_bridge.py                 # 포트 8787, repo 루트 자동
    python tools/qa_bridge.py --port 9000
    QA_BRIDGE_MODEL=sonnet python tools/qa_bridge.py   # 헤드리스 모델 지정
    QA_BRIDGE_SKIP_PERMS=1 python tools/qa_bridge.py   # 권한 우회(편집 막힐 때)

정본: papers 1~26 (2026-07-09).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

VERSION = "1.2"

# repo 루트 = tools/ 의 부모
ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude") or "claude"

# 논문별 동시 생성 방지 락 (folder path str → Lock)
_locks = {}
_locks_guard = threading.Lock()


def folder_lock(key):
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


# ----------------------------- job registry -----------------------------
# 완료된 job 을 얼마나 더 들고 있을지(초). 조회 후에도 남겨 둬야 새로고침·재접속이 산다.
JOB_TTL = 30 * 60
_jobs = {}  # job_id → dict(id, kind, short, status, created, finished, result, log[])
_jobs_guard = threading.Lock()


def _purge_jobs(now=None):
    """만료된 '완료' job 만 정리. running 은 절대 지우지 않는다. (_jobs_guard 안에서 호출)"""
    now = now or time.time()
    for k in [
        k
        for k, j in _jobs.items()
        if j["status"] != "running" and j.get("finished") and now - j["finished"] > JOB_TTL
    ]:
        _jobs.pop(k, None)


def start_job(kind, short, fn, log):
    """fn(log)->result 를 백그라운드 스레드로 실행.

    같은 short 에 대해 running job 이 있으면 **새로 만들지 않고** 그 job 을 돌려준다
    (created=False). 호출자는 job['kind'] 가 요청 kind 와 다르면 busy 로 응답할 것.
    """
    with _jobs_guard:
        _purge_jobs()
        for j in _jobs.values():
            if j["status"] == "running" and j["short"] == short:
                return j, False
        jid = uuid.uuid4().hex[:16]
        job = {
            "id": jid,
            "kind": kind,
            "short": short,
            "status": "running",
            "created": time.time(),
            "finished": None,
            "result": None,
            "log": [],
        }
        _jobs[jid] = job

    def runner():
        def jlog(msg):
            log(msg)
            lines = job["log"]
            lines.append(msg)
            if len(lines) > 60:
                del lines[:-60]

        try:
            res = fn(jlog)
        except Exception as e:
            traceback.print_exc()
            res = {"status": "error", "message": f"서버 예외: {e}"}
        if not isinstance(res, dict):
            res = {"status": "error", "message": "결과 형식 오류"}
        job["result"] = res
        job["finished"] = time.time()
        job["status"] = res.get("status") or "ok"
        log(f"[bridge] job {jid} 완료: {job['status']} - {res.get('message', '')}")

    threading.Thread(target=runner, name=f"job-{jid}", daemon=True).start()
    log(f"[bridge] job {jid} 시작 ({kind}, short={short})")
    return job, True


def job_view(job):
    """job → 클라이언트가 볼 JSON. running 이면 진행 상태, 끝났으면 원래 result 그대로."""
    now = time.time()
    if job["status"] == "running":
        return {
            "status": "running",
            "job_id": job["id"],
            "kind": job["kind"],
            "short": job["short"],
            "elapsed": round(now - job["created"], 1),
            "log_tail": "\n".join(job["log"][-8:]),
        }
    out = dict(job["result"] or {"status": "error", "message": "결과가 비어 있습니다."})
    out["job_id"] = job["id"]
    out["kind"] = job["kind"]
    out["elapsed"] = round((job["finished"] or now) - job["created"], 1)
    out["done"] = True
    return out


def find_paper(short):
    """short('CARES' 등) → papers/N. name 폴더 Path. {short}_output.html 로 매칭.
    배포 킷은 papers 가 비어 있을 수 있어 samples/(정본 samples/cares 등)도 함께 스캔한다."""
    roots = []
    for base in (ROOT / "papers", ROOT / "samples", ROOT):
        if base.is_dir():
            roots.append(base)
    for base in roots:
        for d in sorted(base.iterdir()):
            if d.is_dir() and (d / f"{short}_output.html").exists():
                return d
    return None


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state(folder):
    """.qa_state.json 로드. 구버전 파일에 없는 키는 기본값으로 채운다(하위 호환)."""
    base = {"processed_hash": "", "noop_hash": "", "generated_questions": [], "runs": []}
    p = folder / "study" / ".qa_state.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base.update(data)
                for k, v in [
                    ("processed_hash", ""),
                    ("noop_hash", ""),
                    ("generated_questions", []),
                    ("runs", []),
                ]:
                    if base.get(k) is None:
                        base[k] = v
        except Exception:
            pass
    return base


def hash_gate(state, h):
    """이 메모 해시로 이미 처리한 적이 있으면 nochange 결과, 아니면 None.

    - processed_hash : 실제로 카드를 만들어 완료한 메모.
    - noop_hash      : claude 가 '새 질문 없음' 으로 판정한 메모. 오판 가능성이 있으므로
                       사용자에게 우회(force)를 안내한다(`reason` 로 구분).
    """
    if not h:
        return None
    if h == state.get("processed_hash"):
        return {
            "status": "nochange",
            "reason": "processed",
            "message": "메모가 이전 생성과 동일합니다. (새로 추가된 내용 없음)",
        }
    if h == state.get("noop_hash"):
        return {
            "status": "nochange",
            "reason": "noop",
            "message": "새 질문이 없다고 판정된 메모입니다. 메모를 고치거나 다시 생성할 수 있습니다.",
        }
    return None


def flatten_covers(result):
    """QA_RESULT → 이번 실행이 소화한 '메모 항목' 목록.

    new_cards[*].covers 가 있으면 그것을 평탄화해 우선 사용하고(카드 단위 묶음이라
    new_questions 만으로는 어떤 메모 항목이 소화됐는지 잃는다), 없으면 new_questions.
    """
    cards = result.get("new_cards") or []
    out = []
    if isinstance(cards, list):
        for c in cards:
            if not isinstance(c, dict):
                continue
            for q in c.get("covers") or []:
                q = (q or "").strip()
                if q and q not in out:
                    out.append(q)
    if out:
        return out
    for q in result.get("new_questions") or []:
        q = (q or "").strip()
        if q and q not in out:
            out.append(q)
    return out


def save_state(folder, state):
    d = folder / "study"
    d.mkdir(exist_ok=True)
    (d / ".qa_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def save_study_notes(folder, short, memo):
    """생성 직전 메모를 노트 파일로 저장 - prompts/10_qa.md 가 읽는 형식."""
    d = folder / "study"
    d.mkdir(exist_ok=True)
    ymd = datetime.now().strftime("%y%m%d")
    path = d / f"{short}_study_notes_{ymd}.json"
    payload = {
        "short": short,
        "savedAt": datetime.now().isoformat(timespec="seconds"),
        "source": "qa_bridge",
        "notes": {"memo": memo},
        "memo": memo,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


PROMPT_TEMPLATE = """\
너는 이 저장소(Paper Review HTML Builder)의 Stage 9(Q&A 콘텐츠) + Stage 10(HTML 주입)을 \
비대화형으로 수행한다. 사용자가 학습 중 메모 드로어에 남긴 질문들로부터, 기존 지침에 맞는 \
⑥ Q&A 콘텐츠를 **증분 생성**해 해당 논문 HTML 의 ⑥ tab-qa 섹션에 주입하라.

## 대상 논문
- 폴더: {folder}
- HTML: {folder}/{short}_output.html  (⑥ 탭 = <section id="tab-qa">)
- 데이터: {folder}/structured.json, {folder}/tabs_data/dissection.json, {folder}/tabs_data/knowledge.json
- qa.json(있으면 append, 없으면 생성): {folder}/tabs_data/qa.json

## 반드시 먼저 읽을 지침
- prompts/10_qa.md  (Q&A 스키마·카테고리·작성 원칙·절대 금지 - 그대로 따른다)
- rules/component_rules.md  (§11 codex 5계명, Q&A 위젯 클래스 규약)
- rules/math_rules.md  (수식 부등호 규칙)
- CLAUDE.md 의 "무리한 한국어 변환 금지" 정책

## 반드시 지킬 문체 (CLAUDE.md "감성 온도 0 · 논리 최대")
근거→함의 논리 사슬만. 감탄·평가·응원·과장 수사 금지(흥미롭게도/놀랍게도/훌륭한/우아한/보기 드문/정말/매우 남발/~해봅시다 등).
사실·수치·인과·조건·한계만 남기고, 형용사·부사를 빼도 논리가 유지되면 뺀다. 요약·본문 모두 동일.

## 사용자 메모 (이번 요청 원문)
<<<MEMO
{memo}
MEMO

## 이미 생성한 질문(중복 금지 - 아래와 의미가 겹치는 질문은 새로 만들지 말 것)
{existing}

## 사용 가능한 클래스 (화이트리스트 - 이 목록 밖의 새 클래스를 만들지 말 것)
`.qa-mem-*` CSS 는 tools/qa_button_inject.py 가 이미 HTML 에 주입해 두었다. 아래가 정의된 전부다.
**목록에 없는 클래스를 새로 지어내면 CSS 가 없어 스타일 없는 맨 문단으로 떨어진다.** 필요한 표현이
목록에 없으면 가장 가까운 것을 쓰거나, 클래스 없는 표준 HTML 태그를 쓴다
(`<p>` `<ul>` `<ol>` `<table>` `<strong>` `<em>` `<code>` `<figure>` - 카드 안에서 이미 스타일이 잡혀 있다).
그리고 **새 `<style>` 블록을 파일에 추가하지 않는다** - 필요한 스타일은 전부 아래에 있다.

- `qa-mem-root` - 카드 묶음 컨테이너(div). 메모 쪽은 `data-qa-mem-root`, 검토 쪽은 `data-review-supp`.
- `qa-mem-cat` - 카테고리 라벨(p 또는 h3, 둘 다 같게 렌더). root 바로 아래면 그룹 라벨, 카드 안이면 소제목.
- `qa-mem-card` - 카드(article, `data-qid` 필수).
- `qa-mem-q` - 카드 제목(h3).
- `qa-mem-covers` - 이 카드가 답하는 메모 원문 질문 목록(ul > li).
- `qa-mem-tldr` - 요약 한 문단(p).
- `qa-mem-callout` + `key` / `warn` / `safe` - 강조 박스(div, 예: class="qa-mem-callout key").
- `qa-mem-table-wrap`(div) > `qa-mem-table`(table) - 넓은 표. wrap 이 가로 스크롤을 맡으므로 표는 이 짝으로 쓴다.
- `qa-mem-math` - display 수식 블록(div, 안에 $$...$$).
- `qa-mem-math-note` - 수식 바로 아래 각주 한 문단(p).
- `qa-mem-figcap` - 카드 안 이미지 캡션(figcaption). 이미지는 `<figure>` 안에 둔다.

## 할 일 (증분)
1. **추출** - 메모 텍스트에서 **개별 질문/의문점**을 빠짐없이 뽑는다. 위 '이미 생성한 질문'과 의미가 겹치는 것은 제외.
   남는 새 질문이 없으면 아무 파일도 바꾸지 말고 마지막 줄에 `QA_RESULT: {{"status":"noop","message":"새 질문 없음"}}` 만 출력하고 종료.
1.5 **군집화** - 남은 질문들을 **주제·논리적 연결 기준으로 묶는다.** 한 묶음 = 같은 메커니즘·같은 섹션·같은 주장을
   서로 다른 각도에서 묻고 있는 항목들. **묶음 하나가 카드 하나**가 된다. 연결되는 항목이 없으면 단독 묶음(카드 1장)이다.
   - 억지 병합 금지 - 실제로 연결되지 않는 항목을 한 카드에 몰아넣지 말 것. 근거가 다르고 답의 전제가 공유되지 않으면 별개 묶음이다.
   - 한 묶음의 하위 질문이 5개를 넘으면 논리적 경계(메커니즘 단계·주장 단위)로 쪼갠다.
2. **작성** - 묶음마다 카드 하나. prompts/10_qa.md 의 스키마(qid/title/tldr/blocks)와 작성 원칙에 맞는 Q&A 를 만든다.
   - **개수 상한은 없다.** 메모에서 나온 새 질문은 이번 실행에서 **전부** 다룬다. 다음 생성으로 미루지 않는다.
     카드 수는 상한이 아니라 묶음 수, 즉 메모의 실제 주제 수가 결정한다.
   - 카드 제목(`title`)은 묶음 전체를 포괄하는 **하나의 질문**으로 쓴다.
   - 묶음 카드의 본문은 하위 질문을 따로따로 나열해 각각 답하는 형태가 **아니라 하나의 연결된 설명**이다.
     한 질문의 답이 다음 질문의 전제가 되도록 논리 사슬로 잇고, 각 하위 질문이 본문 어디에서 답해지는지 드러나게 쓴다.
   - 카테고리는 **M - "내가 남긴 질문"**, 각 항목 `"from_memo": true`.
   - 각 카드에 `"covers": ["메모 원문 질문", ...]`(하위 질문 원문 목록)을 남긴다. 하위 질문이 1개면 그 하나만.
   - 본문 근거(§·Table·Fig 번호)를 짚고, 논문이 답하지 않으면 그 사실을 명시.
3. tabs_data/qa.json 을 갱신: 없으면 새로 만들고, 있으면 카테고리 M 에 **append**(기존 항목 유지, qid 중복 금지).
4. 필요한 보조 이미지가 있으면 **codex 로 생성**(rules/component_rules.md §11 5계명 - Bash 로 codex 호출, UTF-8 prompt.txt, ASCII 인자, `< /dev/null`, 스타일·출력 경로 명시).
   저장: {folder}/assets/generated/qa_<qid>_<purpose>.png. 없어도 되면 만들지 말 것(질문당 0~1개).
5. HTML 주입 - {folder}/{short}_output.html 의 <section id="tab-qa"> 안에:
   - `<div class="qa-mem-root" data-qa-mem-root>` 컨테이너를 관리(없으면 .tab-intro 바로 뒤에 생성, 그 섹션에 .section-empty placeholder 가 있으면 제거).
   - 묶음마다 카드 하나 추가: `<article class="qa-mem-card" data-qid="{{qid}}">` 안에
     `<h3 class="qa-mem-q">Q. 제목</h3>`,
     그 **바로 아래** `<ul class="qa-mem-covers"><li>메모 원문 질문</li>…</ul>` - 이 카드가 답하는 메모 항목들.
     **하위 질문이 1개뿐이면 이 블록은 넣지 않는다.**
     이어서 `<p class="qa-mem-tldr">요약 문장만 (…)</p>`(**"TL;DR" 라벨 텍스트 금지** - 요약 문장만 넣는다), 그리고 blocks 를 렌더한 본문.
     (표·수식·callout 블록은 위 '사용 가능한 클래스' 화이트리스트의 클래스만 쓴다. 새 클래스·새 <style> 금지.)
   - **이미 존재하는 data-qid 카드는 다시 만들지 말 것**(HTML 레벨 dedup).
   - 이미지는 CLAUDE.md 자산 임베딩 정책대로 **base64 인라인**.
6. 검증: qa.json 이 유효 JSON 인지, HTML 에 새 data-qid 카드가 실제로 들어갔는지 확인.

## 출력 프로토콜 (필수)
작업이 끝나면 **마지막 줄**에 정확히 아래 형식의 한 줄을 출력한다(그 외 군더더기 금지):
`QA_RESULT: {{"status":"ok","new_cards":[{{"qid":"q7","title":"카드 제목","covers":["메모 원문 질문 1","메모 원문 질문 2"]}}],"new_questions":["메모 원문 질문 1","메모 원문 질문 2", ...],"new_qids":["q7",...],"deferred":0,"images":["assets/generated/.."],"message":"요약"}}`
- `new_cards` - 카드 단위 장부. `covers` 는 그 카드가 답하는 메모 원문 질문 목록.
- `new_questions` - `new_cards` 의 `covers` 를 **전부 평탄하게 나열**한 것(하위 호환 필드). 카드 수가 아니라 질문 수와 같다.
- `deferred` - 이번 실행에서 다루지 못하고 남긴 질문 수. **전부 다루는 것이 원칙이므로 정상값은 0.**
  어떤 이유로든 남겼으면 그 수를 정확히 보고한다(브릿지가 이 값으로 다음 실행의 재시도 여부를 결정한다).
실패 시: `QA_RESULT: {{"status":"error","message":"무엇이 왜 실패"}}`
"""


def build_prompt(folder, short, memo, existing_questions):
    rel = folder.relative_to(ROOT).as_posix()
    if existing_questions:
        existing = "\n".join(f"- {q}" for q in existing_questions)
    else:
        existing = "(아직 없음 - 첫 생성)"
    return PROMPT_TEMPLATE.format(
        folder=rel,
        short=short,
        memo=memo,
        existing=existing,
    )


def run_claude(prompt, log):
    """헤드리스 claude -p 실행. stdout 을 실시간 로그로 흘리고 전체를 반환."""
    model = os.environ.get("QA_BRIDGE_MODEL", "").strip()
    args = [CLAUDE, "-p", "--add-dir", str(ROOT)]
    if os.environ.get("QA_BRIDGE_SKIP_PERMS", "").strip() in ("1", "true", "yes"):
        args += ["--dangerously-skip-permissions"]
    else:
        args += ["--permission-mode", "acceptEdits"]
    if model:
        args += ["--model", model]
    # allowedTools 는 가변인자라 맨 끝에 둔다
    args += ["--allowedTools", "Bash", "Edit", "MultiEdit", "Write", "Read", "Glob", "Grep"]

    log(f"[claude] spawn: {' '.join(args)}")
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(ROOT),
        env=env,
    )
    proc.stdin.write(prompt.encode("utf-8"))
    proc.stdin.close()
    lines = []
    for raw in iter(proc.stdout.readline, b""):
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        lines.append(line)
        log(f"[claude] {line}")
    proc.wait()
    return proc.returncode, lines


def parse_result(lines, marker="QA_RESULT"):
    """stdout 라인들에서 마지막 <marker>: {...} 를 파싱."""
    rx = re.compile(re.escape(marker) + r":\s*(\{.*\})\s*$")
    for line in reversed(lines):
        m = rx.search(line)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                continue
    return None


def generate(short, memo, force, log):
    memo = (memo or "").strip()
    if not memo:
        return {"status": "empty", "message": "메모가 비어 있습니다."}
    folder = find_paper(short)
    if not folder:
        return {"status": "error", "message": f"'{short}_output.html' 논문 폴더를 찾지 못했습니다."}

    lock = folder_lock(str(folder))
    if not lock.acquire(blocking=False):
        return {"status": "busy", "message": "이 논문의 Q&A 를 이미 생성 중입니다. 잠시 후 다시 시도하세요."}
    try:
        state = load_state(folder)
        h = sha(memo)
        if not force:
            gated = hash_gate(state, h)
            if gated is not None:
                return gated

        notes_path = save_study_notes(folder, short, memo)
        log(f"[bridge] study notes saved: {notes_path.name}")

        existing = state.get("generated_questions", [])
        prompt = build_prompt(folder, short, memo, existing)
        rc, lines = run_claude(prompt, log)
        result = parse_result(lines)
        if result is None:
            return {
                "status": "error",
                "message": f"헤드리스 claude 결과를 파싱하지 못했습니다 (exit {rc}). 브릿지 콘솔 로그를 확인하세요.",
            }
        if result.get("status") == "ok":
            covered = flatten_covers(result)
            cards = result.get("new_cards") or []
            try:
                deferred = int(result.get("deferred") or 0)
            except (TypeError, ValueError):
                deferred = 0
            state["generated_questions"] = existing + [q for q in covered if q not in existing]
            # 🔴 남긴 질문이 있으면 processed_hash 를 갱신하지 않는다 -
            #    같은 메모로 다시 눌러 나머지를 이어받을 수 있어야 한다.
            if deferred <= 0:
                state["processed_hash"] = h
            if state.get("noop_hash") == h:
                state["noop_hash"] = ""  # 새 질문이 실제로 나왔으므로 noop 판정 철회
            state.setdefault("runs", []).append(
                {
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "new_qids": result.get("new_qids", []),
                    "new_count": len(covered),
                    "card_count": len(cards) if isinstance(cards, list) else 0,
                    "covered_count": len(covered),
                    "deferred": deferred,
                }
            )
            save_state(folder, state)
        elif result.get("status") == "noop":
            # 🔴 processed_hash 는 건드리지 않는다 - claude 가 새 질문을 중복으로 오판했을 때
            #    그 메모가 영구 차단되면 안 된다. 대신 noop_hash 에만 기록해 재실행 비용을 막고,
            #    클라이언트는 '그래도 다시 생성' 우회를 노출한다.
            state["noop_hash"] = h
            state.setdefault("runs", []).append(
                {
                    "at": datetime.now().isoformat(timespec="seconds"),
                    "new_qids": [],
                    "new_count": 0,
                    "card_count": 0,
                    "covered_count": 0,
                    "deferred": 0,
                    "status": "noop",
                }
            )
            save_state(folder, state)
        return result
    finally:
        lock.release()


def gen_precheck(short, memo, force):
    """claude 를 돌리지 않고 즉답할 수 있는 경우만 result 를 돌려준다(아니면 None).

    job 으로 만들 가치가 없는 빠른 경로(empty / 폴더 없음 / nochange)를 걸러 낸다.
    generate() 안에서 같은 검사를 다시 하므로 동기 경로와 판정이 어긋나지 않는다.
    """
    memo = (memo or "").strip()
    if not memo:
        return {"status": "empty", "message": "메모가 비어 있습니다."}
    folder = find_paper(short)
    if not folder:
        return {"status": "error", "message": f"'{short}_output.html' 논문 폴더를 찾지 못했습니다."}
    if not force:
        gated = hash_gate(load_state(folder), sha(memo))
        if gated is not None:
            return gated
    return None


REVIEW_PROMPT_TEMPLATE = """\
너는 이 저장소의 Paper Study 답변 검토자다. 학습자가 Paper Study 탭에 쓴 답변을, \
study.json 에 담긴 **Claude 기준 분석**과 대조해 단계별 피드백을 만들고, 약한 부분을 \
⑥ Q&A 탭에 보완 학습 카드로 보충한다. 비대화형으로 수행한다.

## 대상 논문
- 폴더: {folder}
- 기준 분석: {folder}/tabs_data/study.json  (각 단계의 claude_html / claude_items / claude_dataonly_summary / author_claims 가 '정답 관점')
- 근거 대조: {folder}/structured.json (문장/자산 id → 근거 refs)
- HTML: {folder}/{short}_output.html  (⑥ 탭 = <section id="tab-qa">)

## 반드시 지킬 문체 (CLAUDE.md "감성 온도 0 · 논리 최대")
근거→함의 논리 사슬만. 감탄·평가·응원·과장 수사 금지(흥미롭게도/놀랍게도/훌륭한/보기 드문/정말/매우 남발 등).
사실·수치·인과·조건·한계만. 형용사를 빼도 논리가 유지되면 뺀다.

## 학습자 답변 (skey → 작성 내용)
<<<ANSWERS
{answers}
ANSWERS

## skey ↔ 기준 분석 대응
- rq → phase1.rq.claude_html
- gap_known / gap_hole / gap_fill → phase1.gap.claude_html (세 칸을 합쳐 하나의 Gap 논증으로 평가)
- method → phase2.method.claude_html
- conclusion → phase2.conclusion.claude_html
- alt → phase3.alternatives.claude_items (+ phase3.verdict 의 author_claims 대조도 참고)

## 사용 가능한 클래스 (화이트리스트 - 이 목록 밖의 새 클래스를 만들지 말 것)
`.qa-mem-*` CSS 는 tools/qa_button_inject.py 가 이미 HTML 에 주입해 두었다. 아래가 정의된 전부다.
**목록에 없는 클래스를 새로 지어내면 CSS 가 없어 스타일 없는 맨 문단으로 떨어진다.** 필요한 표현이
목록에 없으면 가장 가까운 것을 쓰거나, 클래스 없는 표준 HTML 태그를 쓴다
(`<p>` `<ul>` `<ol>` `<table>` `<strong>` `<em>` `<code>` `<figure>` - 카드 안에서 이미 스타일이 잡혀 있다).
그리고 **새 `<style>` 블록을 파일에 추가하지 않는다** - 필요한 스타일은 전부 아래에 있다.

- `qa-mem-root` - 카드 묶음 컨테이너(div). 메모 쪽은 `data-qa-mem-root`, 검토 쪽은 `data-review-supp`.
- `qa-mem-cat` - 카테고리 라벨(p 또는 h3, 둘 다 같게 렌더). root 바로 아래면 그룹 라벨, 카드 안이면 소제목.
- `qa-mem-card` - 카드(article, `data-qid` 필수).
- `qa-mem-q` - 카드 제목(h3).
- `qa-mem-covers` - 이 카드가 답하는 메모 원문 질문 목록(ul > li).
- `qa-mem-tldr` - 요약 한 문단(p).
- `qa-mem-callout` + `key` / `warn` / `safe` - 강조 박스(div, 예: class="qa-mem-callout key").
- `qa-mem-table-wrap`(div) > `qa-mem-table`(table) - 넓은 표. wrap 이 가로 스크롤을 맡으므로 표는 이 짝으로 쓴다.
- `qa-mem-math` - display 수식 블록(div, 안에 $$...$$).
- `qa-mem-math-note` - 수식 바로 아래 각주 한 문단(p).
- `qa-mem-figcap` - 카드 안 이미지 캡션(figcaption). 이미지는 `<figure>` 안에 둔다.

## 할 일
1. **단계별 검토** - 작성된 각 skey 에 대해:
   - `match`(0~100 정합도): 학습자 답이 기준 분석의 핵심 논점을 얼마나 포착했는지. 근거 없는 후한 점수 금지.
   - `aligned`: 학습자가 **맞게** 파악한 지점(학습자 표현을 짚어 1~3개).
   - `misread`: **어떤 관점에서 잘못/편향되게** 파악했는지. 각 항목 {{point, why(왜 어긋났는지 - 논리·근거 기준), evidence:[{{label, ref}}]}}. ref 는 study.json/structured.json 의 실제 sentence_id·자산 id.
   - `missing`: 기준 분석엔 있으나 학습자가 **다루지 않은** 핵심 논점(0~3개).
   - `verdict`: 한 문장 논리적 총평.
   - gap_* 세 칸이 있으면 skey 를 "gap" 하나로 합쳐 평가(label "Gap 파악").
2. **약한 skey 선정** - match < 60 이거나 중대한 misread 가 있는 skey 를 `weak_skeys` 로.
3. **보완 학습 주입** - 약한 부분을 스스로 학습하도록, 그 논점의 **기초부터 설명하는** Q&A 카드를 만든다:
   - 카테고리 W "보완 학습". prompts/10_qa.md 의 blocks 스키마(html/table/math/callout) 준수. 질문당 한 줄 요약(tldr) 먼저 - "TL;DR" 라벨 텍스트는 렌더하지 않는다.
   - {folder}/tabs_data/qa.json 의 카테고리 W 를 **이번 검토 결과로 교체**(누적 아님). 없으면 생성.
   - HTML {folder}/{short}_output.html 의 <section id="tab-qa"> 안에 `<div class="qa-mem-root" data-review-supp>` 를 **관리(내용 교체)**: 없으면 .tab-intro 뒤(또는 기존 data-qa-mem-root 뒤)에 생성하고 .section-empty 제거. 그 안에 `<h3 class="qa-mem-cat">보완 학습 - 검토에서 약했던 부분</h3>` + 약한 논점마다 `<article class="qa-mem-card" data-qid="w1">`(qa-mem-q/qa-mem-tldr/본문). 이미지가 꼭 필요하면 codex(§11)로 만들어 base64 인라인, 없으면 만들지 말 것. `data-review-supp` 컨테이너는 매 실행마다 내용 전체 교체(중복 누적 금지).
   - 약한 skey 가 없으면 보완 카드는 만들지 않는다(qa_added=0).
4. 검증: study.json 근거 ref 실존, qa.json 유효, HTML 에 data-review-supp 반영.

## 출력 프로토콜 (필수 - 마지막 줄 한 줄)
`STUDY_REVIEW_RESULT: {{"status":"ok","feedback":[{{"skey":"rq","label":"핵심 연구 질문","match":72,"aligned":["..."],"misread":[{{"point":"..","why":"..","evidence":[{{"label":"..","ref":".."}}]}}],"missing":[".."],"verdict":".."}}],"weak_skeys":["gap"],"qa_added":2,"new_qids":["w1","w2"],"message":"요약"}}`
실패 시: `STUDY_REVIEW_RESULT: {{"status":"error","message":"무엇이 왜"}}`
"""


def build_review_prompt(folder, short, answers):
    lines = []
    for k, v in answers.items():
        v = (v or "").strip()
        if v:
            lines.append(f"[{k}]\n{v}")
    ans = "\n\n".join(lines) if lines else "(작성된 답변 없음)"
    return REVIEW_PROMPT_TEMPLATE.format(
        folder=folder.relative_to(ROOT).as_posix(),
        short=short,
        answers=ans,
    )


def generate_review(short, answers, log):
    answers = {k: v for k, v in (answers or {}).items() if (v or "").strip()}
    if not answers:
        return {"status": "empty", "message": "작성된 답변이 없습니다. Paper Study를 먼저 채워 주세요."}
    folder = find_paper(short)
    if not folder:
        return {"status": "error", "message": f"'{short}_output.html' 논문 폴더를 찾지 못했습니다."}
    if not (folder / "tabs_data" / "study.json").exists():
        return {"status": "error", "message": "이 논문에는 study.json(기준 분석)이 없어 검토할 수 없습니다."}

    lock = folder_lock(str(folder))
    if not lock.acquire(blocking=False):
        return {"status": "busy", "message": "이미 처리 중입니다. 잠시 후 다시 시도하세요."}
    try:
        # 입력 스냅샷 저장
        d = folder / "study"
        d.mkdir(exist_ok=True)
        (d / ".study_review_input.json").write_text(
            json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        prompt = build_review_prompt(folder, short, answers)
        rc, out = run_claude(prompt, log)
        result = parse_result(out, marker="STUDY_REVIEW_RESULT")
        if result is None:
            return {"status": "error", "message": f"검토 결과 파싱 실패 (exit {rc}). 브릿지 콘솔 로그 확인."}
        if result.get("status") == "ok":
            (d / ".study_review.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        return result
    finally:
        lock.release()


def review_precheck(short, answers):
    """검토 요청의 빠른 실패 경로만 판정(아니면 None)."""
    answers = {k: v for k, v in (answers or {}).items() if (v or "").strip()}
    if not answers:
        return {"status": "empty", "message": "작성된 답변이 없습니다. Paper Study를 먼저 채워 주세요."}
    folder = find_paper(short)
    if not folder:
        return {"status": "error", "message": f"'{short}_output.html' 논문 폴더를 찾지 못했습니다."}
    if not (folder / "tabs_data" / "study.json").exists():
        return {"status": "error", "message": "이 논문에는 study.json(기준 분석)이 없어 검토할 수 없습니다."}
    return None


# ----------------------------- HTTP -----------------------------
# 클라이언트가 먼저 끊고 간 경우(긴 작업 + 브라우저 타임아웃). 작업 자체는 이미 끝났고
# 결과도 파일/ job 에 남아 있으므로 트레이스백을 찍을 이유가 없다.
DISCONNECT_ERRORS = (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)


class Handler(BaseHTTPRequestHandler):
    server_version = "qa_bridge/" + VERSION

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(code)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except DISCONNECT_ERRORS:
            self.close_connection = True
            print("[bridge] client disconnected (result already saved)", flush=True)
        except OSError as e:  # WinError 10053/10054 가 OSError 로만 올라오는 경우 대비
            self.close_connection = True
            print(f"[bridge] client disconnected while writing ({e})", flush=True)

    def log_message(self, fmt, *args):
        pass  # 우리 자체 로그만 쓴다

    def do_OPTIONS(self):
        try:
            self.send_response(204)
            self._cors()
            self.end_headers()
        except (OSError,) + DISCONNECT_ERRORS:
            self.close_connection = True

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/job" or path.startswith("/job/"):
            jid = ""
            if path.startswith("/job/"):
                jid = path[len("/job/"):]
            if not jid:
                jid = (parse_qs(parsed.query).get("id") or [""])[0]
            jid = jid.strip()
            with _jobs_guard:
                _purge_jobs()
                job = _jobs.get(jid)
            if not job:
                self._json(
                    404,
                    {
                        "status": "unknown",
                        "job_id": jid,
                        "message": "그 job 을 찾을 수 없습니다 (브릿지 재시작 또는 보관 기간 만료).",
                    },
                )
            else:
                self._json(200, job_view(job))
            return
        if path in ("/ping", ""):
            # find_paper 와 동일한 검색 루트(papers/ + samples/) - 배포 킷은 papers 가 비어
            # 정본이 samples/cares 에 있으므로 함께 열거한다.
            papers = []
            for base in (ROOT / "papers", ROOT / "samples"):
                if base.is_dir():
                    for d in sorted(base.iterdir()):
                        if d.is_dir():
                            for f in d.glob("*_output.html"):
                                papers.append(f.name.replace("_output.html", ""))
            self._json(200, {"ok": True, "version": VERSION, "papers": papers})
        else:
            self._json(404, {"ok": False, "message": "unknown path"})

    def do_POST(self):
        path = self.path.rstrip("/")
        if path not in ("/gen-qa", "/review-study"):
            self._json(404, {"status": "error", "message": "unknown path"})
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n).decode("utf-8") if n else "{}"
            data = json.loads(raw)
        except Exception as e:
            self._json(400, {"status": "error", "message": f"잘못된 요청: {e}"})
            return
        short = (data.get("short") or "").strip()
        if not short:
            self._json(400, {"status": "error", "message": "short 누락"})
            return

        def log(msg):
            stamp = time.strftime("%H:%M:%S")
            print(f"{stamp} {msg}", flush=True)

        memo = data.get("memo") or ""
        force = bool(data.get("force"))
        answers = data.get("answers") or {}
        if path == "/gen-qa":
            kind = "gen-qa"
            log(f"[bridge] /gen-qa short={short} force={force} memo_len={len(memo)}")
            pre = lambda: gen_precheck(short, memo, force)  # noqa: E731
            work = lambda jlog: generate(short, memo, force, jlog)  # noqa: E731
        else:
            kind = "review-study"
            log(f"[bridge] /review-study short={short} answers={list(answers.keys())}")
            pre = lambda: review_precheck(short, answers)  # noqa: E731
            work = lambda jlog: generate_review(short, answers, jlog)  # noqa: E731

        # 새 클라이언트만 async 를 보낸다. 없으면 예전처럼 동기 응답(구버전 HTML 하위 호환).
        want_async = bool(data.get("async")) and not bool(data.get("sync"))

        if want_async:
            try:
                fast = pre()
            except Exception as e:
                traceback.print_exc()
                fast = {"status": "error", "message": f"서버 예외: {e}"}
            if fast is not None:
                # claude 를 돌리지 않는 빠른 경로 - job 으로 만들지 않고 그 자리에서 200.
                log(f"[bridge] fast: {fast.get('status')} - {fast.get('message', '')}")
                self._json(200, fast)
                return
            job, created = start_job(kind, short, work, log)
            if job["kind"] != kind:
                self._json(
                    200,
                    {
                        "status": "busy",
                        "message": "이 논문에 대해 다른 작업이 진행 중입니다. 끝난 뒤 다시 시도하세요.",
                        "job_id": job["id"],
                    },
                )
                return
            if not created:
                log(f"[bridge] job {job['id']} 재사용 (이미 실행 중 - 중복 실행 차단)")
            self._json(
                202,
                {
                    "status": "accepted",
                    "job_id": job["id"],
                    "kind": kind,
                    "reused": not created,
                    "message": "작업을 접수했습니다. GET /job?id= 로 상태를 확인하세요.",
                },
            )
            return

        # ---- 레거시 동기 경로 ----
        try:
            result = work(log)
        except Exception as e:
            traceback.print_exc()
            result = {"status": "error", "message": f"서버 예외: {e}"}
        log(f"[bridge] result: {result.get('status')} - {result.get('message', '')}")
        self._json(200, result)


class BridgeServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        """끊긴 연결은 트레이스백 없이 한 줄만. (긴 작업 + 브라우저 타임아웃의 정상 결과)"""
        exc = sys.exc_info()[1]
        if isinstance(exc, DISCONNECT_ERRORS):
            print("[bridge] client disconnected (result already saved)", flush=True)
            return
        super().handle_error(request, client_address)


def main():
    # Windows 콘솔(cp949)에서 한글·em-dash 출력이 죽지 않도록 UTF-8 로 재설정
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="메모 Q&A 생성 로컬 브릿지")
    ap.add_argument("--port", type=int, default=int(os.environ.get("QA_BRIDGE_PORT", "8787")))
    ap.add_argument("--host", default="127.0.0.1")
    # qabridge:// 프로토콜 실행 시 URL 이 인자로 붙어 오므로 알 수 없는 인자는 무시
    args, _unknown = ap.parse_known_args()

    if not (ROOT / "papers").is_dir() and not list(ROOT.glob("*/*_output.html")):
        print(f"[warn] papers 폴더를 {ROOT} 아래에서 찾지 못했습니다. --add-dir 확인 필요.")

    try:
        srv = BridgeServer((args.host, args.port), Handler)
    except OSError as e:
        # 이미 다른 인스턴스가 그 포트를 쓰는 중 - 프로토콜 재실행 등. 조용히 종료.
        print(f"포트 {args.port} 를 열 수 없습니다 (브릿지가 이미 실행 중일 수 있습니다): {e}")
        return
    print(f"qa_bridge {VERSION} - http://{args.host}:{args.port}")
    print(f"  repo root : {ROOT}")
    print(f"  claude    : {CLAUDE}")
    print(f"  model     : {os.environ.get('QA_BRIDGE_MODEL') or '(inherit)'}")
    print(f"  skip-perms: {os.environ.get('QA_BRIDGE_SKIP_PERMS') or '0'}")
    print("  endpoints : GET /ping · GET /job?id= · POST /gen-qa · POST /review-study")
    print("  jobs      : async=1 요청은 202+job_id 로 접수, 결과는 /job 폴링 (완료 후 30분 보관)")
    print("  Ctrl+C 로 종료. 메모 드로어의 'Q&A 생성' 버튼이 이 서버로 요청합니다.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
        srv.shutdown()


if __name__ == "__main__":
    main()
