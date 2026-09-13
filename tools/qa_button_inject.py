# -*- coding: utf-8 -*-
"""qa_button_inject.py - 메모 플로팅 드로어에 'Q&A 생성' 버튼을 주입.

메모 드로어(.memo-drawer/.memo-pad/.memo-status)는 자립형(memo_inject.py, papers 1~3)
이든 CARES-통합형(papers 4~26)이든 **동일 클래스**를 쓴다. 그래서 이 도구는 런타임에
JS 로 `.memo-drawer` 를 찾아 버튼 바를 붙이는 방식으로 26편 전체를 균일 처리한다
(기존 마크업·콘텐츠 무변경, additive, idempotent).

버튼 동작
--------
- 클릭 → 로컬 브릿지(tools/qa_bridge.py, 기본 http://127.0.0.1:8787)에 현재 메모 전송
  → 브릿지가 헤드리스 claude 로 ⑥ Q&A 탭에 증분 주입.
- **내용 무손실**: 메모 textarea/localStorage 는 절대 비우지 않는다. 새로고침 전에도 저장.
- **중복 방지**: 클라이언트 해시(djb2)로 "메모 변경 없음"이면 재요청 대신 안내(+'다시 생성' 우회).
  서버도 sha256 해시로 이중 차단하고, 헤드리스 claude 는 이미 생성한 질문과 의미 겹침을 dedup.
- **우아한 실패**: 브릿지가 꺼져 있으면 /ping 실패를 잡아 실행 방법을 안내.
- **비동기 job 폴링 (v2, 2026-09-10)**: 헤드리스 claude 는 10분을 넘기는 일이 흔하다.
  한 번의 fetch 로 끝까지 기다리면 브라우저가 먼저 끊어 **성공한 작업이 실패로 보인다**.
  그래서 요청에 `async:1` 을 붙여 202 + job_id 만 받고 `GET /job?id=` 를 2.5초 간격으로
  폴링한다(개별 fetch 10초, 전체 상한 40분). job_id 는 localStorage(`prstudy:{SHORT}:qa_job`)
  에 남겨 **새로고침·탭 재오픈 후 진행 중이던 작업에 다시 붙는다**. 상한을 넘겨도 "중단됨"
  이라 하지 않는다 - 서버는 계속 돌고 있을 수 있으므로 그 사실과 재접속 방법을 안내한다.

- **묶음 카드 + 상한 제거 (v3, 2026-09-10)**: 브릿지 프롬프트가 메모 질문을 주제별로 묶어
  **한 카드에 연결된 설명**으로 답하도록 바뀌었다(개수 상한 없음). 카드가 답하는 메모 원문
  질문들은 `<ul class="qa-mem-covers">` 로 헤더 아래 표시되므로 그 CSS 를 함께 주입한다.
  상태 표시도 "질문 N개 → 카드 M장"으로 바꾸고, 서버가 `deferred>0`(남긴 질문 있음) 이나
  `nochange{reason:"noop"}` 를 보내면 **클라이언트 해시를 봉인하지 않고 '그래도 다시 생성'**
  우회를 노출한다 - 정당한 새 질문이 해시로 영구 차단되는 경로를 없애기 위해서다.

또한 ⑥ tab-qa 에 헤드리스 claude 가 써넣을 카드용 `.qa-mem-*` CSS 를 함께 주입한다
(스타일을 파일에 고정 → 헤드리스 런은 클래스만 맞추면 됨).

사용법:  python tools/qa_button_inject.py "papers/N. shortname"
        python tools/qa_button_inject.py --all        # papers 전체
검증  :  재실행 시 이미 있으면 skip (idempotent).

정본: papers 1~26 (2026-07-09) · v2 비동기 job (2026-09-10) · v3 묶음 카드(.qa-mem-covers) + noop 우회 안내 (2026-09-10, 모체 papers 1~35 — 배포본 미포함).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

QA_CSS = """
/* ==== 메모 Q&A 생성 버튼 (qa_button_inject.py) v4 ==== */
.qa-gen-bar{margin:0 18px 4px;display:flex;flex-direction:column;gap:7px}
.qa-gen-btn{font:inherit;font-size:13px;font-weight:800;color:#ffffff;background:var(--accent);border:1px solid var(--accent);border-radius:9px;padding:9px 12px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px}
.qa-gen-btn:hover{filter:brightness(1.06)}
.qa-gen-btn:disabled{opacity:.55;cursor:default}
.qa-gen-btn .qa-spin{width:13px;height:13px;border:2px solid rgba(255,255,255,.45);border-top-color:#fff;border-radius:50%;display:none;animation:qa-spin 0.8s linear infinite}
.qa-gen-btn.busy .qa-spin{display:inline-block}
@keyframes qa-spin{to{transform:rotate(360deg)}}
.qa-gen-status{font-size:11.5px;line-height:1.6;color:var(--muted);min-height:1.2em}
.qa-gen-status.ok{color:var(--mint)}
.qa-gen-status.err{color:var(--rose)}
.qa-gen-status a,.qa-gen-status button.qa-link{color:var(--accent);font:inherit;font-size:11.5px;font-weight:700;background:none;border:none;padding:0;cursor:pointer;text-decoration:underline}
/* ==== ⑥ tab-qa 메모 생성 카드 (헤드리스 claude 가 채움) ==== */
.qa-mem-root{display:flex;flex-direction:column;gap:16px;margin-top:10px}
.qa-mem-card{border:1px solid var(--line);border-radius:12px;padding:16px 18px;background:var(--paper);box-shadow:var(--shadow)}
.qa-mem-card .qa-mem-q{margin:0 0 8px;font-size:15px;font-weight:800;color:var(--accent)}
/* 묶음 카드가 답하는 메모 원문 질문 목록 (하위 질문 2개 이상일 때만 렌더) */
.qa-mem-card .qa-mem-covers{margin:0 0 10px;padding:7px 12px 7px 27px;list-style:disc;border:1px dashed var(--line);border-radius:8px;background:transparent}
.qa-mem-card .qa-mem-covers li{font-size:12px;line-height:1.6;color:var(--muted);margin:2px 0}
.qa-mem-card .qa-mem-covers li::marker{color:var(--accent-mid)}
.qa-mem-card .qa-mem-tldr{margin:0 0 10px;font-size:13.5px;background:var(--accent-soft);border-radius:8px;padding:9px 12px;color:var(--ink);line-height:1.65}
.qa-mem-card p{font-size:13.5px;line-height:1.75;color:var(--ink)}
.qa-mem-card table{border-collapse:collapse;font-size:12.5px;margin:8px 0;width:100%}
.qa-mem-card th,.qa-mem-card td{border:1px solid var(--line);padding:5px 9px;text-align:left}
.qa-mem-card th{background:var(--accent-soft)}
.qa-mem-callout{border-radius:9px;padding:10px 13px;font-size:13px;line-height:1.7;margin:8px 0}
.qa-mem-callout.key{background:var(--mint-soft);border:1px solid var(--mint)}
.qa-mem-callout.warn{background:var(--rose-soft);border:1px solid var(--rose)}
.qa-mem-callout.safe{background:var(--accent-soft);border:1px solid var(--accent-mid)}
.qa-mem-card figure{margin:10px 0}
.qa-mem-card figure img{max-width:100%;border-radius:9px;border:1px solid var(--line)}
/* ==== ⑥ tab-qa 보조 클래스 (v4, 2026-09-10) - 카테고리 라벨 · 표 · 수식 · 캡션 ====
   헤드리스 run 이 만들어 쓰던 미정의 클래스(qa-mem-cat / qa-mem-figcap / qa-mem-math /
   qa-mem-math-note)를 여기서 확정한다. 브릿지 프롬프트의 화이트리스트와 1:1 로 대응하며,
   목록 밖 클래스를 새로 만들지 않는 것이 그 프롬프트의 규약이다. */
.qa-mem-root+.qa-mem-root,.qa-mem-root[data-review-supp]{margin-top:18px}
.qa-mem-root>.qa-mem-card{min-width:0}
/* 카테고리 라벨. <p> 와 <h3> 가 같은 클래스를 쓰므로(메모 쪽 p · 검토 쪽 h3)
   태그 기본값 margin·font-size·font-weight 를 명시 리셋해 두 태그 렌더를 일치시킨다. */
.qa-mem-cat,.qa-mem-card .qa-mem-cat,.qa-mem-root>.qa-mem-cat{display:block;box-sizing:border-box;margin:14px 0 8px;padding:0;font-family:inherit;font-size:12px;font-weight:800;line-height:1.5;letter-spacing:.04em;color:var(--accent);text-align:left}
.qa-mem-card .qa-mem-cat:first-child{margin-top:0}
/* 카드 묶음 위의 그룹 라벨. 아래 카드들과 한 덩어리로 읽히도록 구분선 하나만 둔다(좌측 색 띠 금지). */
.qa-mem-root>.qa-mem-cat{margin:0;padding:0 2px 9px;font-size:12.5px;color:var(--ink-soft);border-bottom:1px solid var(--line)}
/* 표. 카드 폭을 넘으면 페이지가 아니라 표가 스크롤한다. */
.qa-mem-table-wrap{overflow-x:auto;max-width:100%;margin:10px 0}
.qa-mem-card .qa-mem-table{border-collapse:collapse;width:100%;font-size:12.5px;margin:0}
/* display 수식. v4 규약대로 배경은 다크가 아니라 밝은 회색이고, 넘치면 자체 스크롤한다. */
.qa-mem-math,.qa-mem-card .qa-mem-math{margin:12px 0;padding:14px;background:#f1f2f7;border:1px solid var(--line);border-radius:10px;color:var(--ink);font-size:15.5px;line-height:1.5;max-width:100%;overflow-x:auto;overflow-y:hidden;scrollbar-width:thin}
.qa-mem-card .qa-mem-math mjx-container[display]{margin:0}
.qa-mem-math-note,.qa-mem-card .qa-mem-math-note{margin:-2px 0 10px;font-size:12.5px;font-weight:400;line-height:1.65;color:var(--ink-soft)}
/* 카드 안 이미지 캡션. .diss-overview-figure figcaption 관례(좌측 정렬 · muted)를 따른다. */
.qa-mem-figcap,.qa-mem-card .qa-mem-figcap{display:block;margin:8px 0 0;font-size:12.5px;font-weight:400;line-height:1.6;color:var(--muted);text-align:left}
@media print{.qa-gen-bar{display:none !important}}
"""

QA_JS = r"""
<script>
/* ==== 메모 Q&A 생성 버튼 (qa_button_inject.py) v3 - 비동기 job 폴링 + qabridge:// 자동 시작 + 묶음 카드/해시 우회 ==== */
(function(){
  var SHORT = "__SHORT__";
  function bridgeUrl(){
    try { return localStorage.getItem("prstudy:qa_bridge_url") || "http://127.0.0.1:8787"; }
    catch(e){ return "http://127.0.0.1:8787"; }
  }
  function fetchT(url, opts, ms){
    var ctl = new AbortController();
    var t = setTimeout(function(){ ctl.abort(); }, ms);
    opts = opts || {}; opts.signal = ctl.signal;
    return fetch(url, opts).finally(function(){ clearTimeout(t); });
  }

  /* ---- 공용: 브릿지가 켜져 있는지 확인하고, 꺼져 있으면 qabridge:// 로 자동 시작 후 대기 ---- */
  if(!window.__qaBridgeEnsure){
    window.__qaBridgeEnsure = function(onReady, onStatus){
      var url = bridgeUrl();
      function ping(){ return fetchT(url + '/ping', {method:'GET'}, 2000).then(function(r){ return !!(r && r.ok); }).catch(function(){ return false; }); }
      ping().then(function(up){
        if(up){ onReady(true); return; }
        if(onStatus) onStatus('브릿지를 켜는 중… 브라우저가 “열기”를 물으면 <b>허용</b>해 주세요. (최초 1회)');
        try {
          var f = document.getElementById('__qa_bridge_frame');
          if(!f){ f = document.createElement('iframe'); f.id = '__qa_bridge_frame'; f.style.display = 'none'; document.body.appendChild(f); }
          f.src = 'qabridge://start?t=' + (new Date().getTime());
        } catch(e){}
        var tries = 0;
        (function poll(){
          setTimeout(function(){
            ping().then(function(u2){
              if(u2){ onReady(true); }
              else if(++tries < 20){ if(onStatus) onStatus('브릿지 시작을 기다리는 중… (' + tries + ')'); poll(); }
              else { onReady(false); }
            });
          }, 800);
        })();
      });
    };
  }

  /* ---- 공용: 비동기 job 접수 + 폴링 (qa_button_inject / study_review_inject 공유, v2) ----
     헤드리스 claude 는 10분을 넘기는 일이 흔하다. 한 번의 fetch 로 끝까지 기다리면
     브라우저 타임아웃·탭 이동에 결과를 잃으므로, 202 로 job_id 만 받고 /job 을 폴링한다.
     job_id 는 localStorage 에 남겨 새로고침·재오픈 후에도 같은 작업에 다시 붙는다. */
  if(!window.__qaBridgeJob2){
    window.__qaBridgeJob2 = function(o){
      /* o = {path, body, jobKey, running(text)->html, onStatus(html,cls), onResult(res),
              onGiveUp(), onLost(), onError(err), resumeOnly} */
      var POLL_MS = 2500, FETCH_MS = 10000, MAXWAIT = 40 * 60 * 1000;
      function bu(){ try { return localStorage.getItem("prstudy:qa_bridge_url") || "http://127.0.0.1:8787"; } catch(e){ return "http://127.0.0.1:8787"; } }
      function ft(url, opts, ms){ var c = new AbortController(); var t = setTimeout(function(){ c.abort(); }, ms); opts = opts || {}; opts.signal = c.signal; return fetch(url, opts).finally(function(){ clearTimeout(t); }); }
      function jset(v){ try { if(v) localStorage.setItem(o.jobKey, v); else localStorage.removeItem(o.jobKey); } catch(e){} }
      function jget(){ try { return localStorage.getItem(o.jobKey) || ""; } catch(e){ return ""; } }
      function fmt(sec){ sec = Math.max(0, Math.round(sec || 0)); var m = Math.floor(sec / 60), s = sec % 60; return m ? (m + '분 ' + s + '초') : (s + '초'); }
      var t0 = Date.now(), stopped = false, first = true;
      function done(res){ if(stopped) return; stopped = true; jset(''); o.onResult(res); }
      function poll(id){
        if(stopped) return;
        if(Date.now() - t0 > MAXWAIT){ stopped = true; if(o.onGiveUp) o.onGiveUp(); return; }
        ft(bu() + '/job?id=' + encodeURIComponent(id), {method:'GET'}, FETCH_MS)
          .then(function(r){ return r.json(); })
          .then(function(j){
            first = false;
            if(j.status === 'running'){ o.onStatus(o.running(fmt(j.elapsed))); setTimeout(function(){ poll(id); }, POLL_MS); }
            else if(j.status === 'unknown'){ stopped = true; jset(''); if(o.onLost) o.onLost(); }
            else done(j);
          })
          .catch(function(){
            /* 일시적 불통이면 계속 재시도한다. 다만 '복원' 중 첫 조회가 실패하면 브릿지가
               꺼진 것이고 job 은 메모리에만 살아 있으므로 조용히 포기한다. */
            if(first && o.resumeOnly){ stopped = true; jset(''); return; }
            first = false;
            o.onStatus(o.running(fmt((Date.now() - t0) / 1000)) + ' (브릿지 응답 대기…)');
            setTimeout(function(){ poll(id); }, POLL_MS);
          });
      }
      if(o.resumeOnly){
        var old = jget();
        if(!old) return false;
        o.onStatus(o.running('…'));
        poll(old);
        return true;
      }
      var body = o.body || {};
      body.async = 1;              /* 새 클라이언트 표식 - 없으면 브릿지가 동기 응답(구버전 호환) */
      ft(bu() + o.path, {method:'POST', headers:{'Content-Type':'text/plain;charset=UTF-8'}, body: JSON.stringify(body)}, 20000)
        .then(function(r){ return r.json(); })
        .then(function(res){
          if(res && res.status === 'accepted' && res.job_id){
            jset(res.job_id); t0 = Date.now(); o.onStatus(o.running('0초')); poll(res.job_id);
          } else {
            done(res || {status:'error', message:'브릿지가 빈 응답을 보냈습니다.'});  /* 200 즉답(nochange 등) */
          }
        })
        .catch(function(err){ stopped = true; if(o.onError) o.onError(err); });
      return true;
    };
  }

  var HKEY = "prstudy:" + SHORT + ":qa_client_hash";
  var MEMOKEY = "prstudy:" + SHORT + ":memo";
  var JOBKEY = "prstudy:" + SHORT + ":qa_job";          /* 진행 중 job_id - 새로고침 후 재접속용 */
  var PHKEY = "prstudy:" + SHORT + ":qa_pending_hash";  /* 요청 시점 메모 해시(완료 때 확정) */
  function hget(){ try { return localStorage.getItem(HKEY) || ""; } catch(e){ return ""; } }
  function hset(v){ try { localStorage.setItem(HKEY, v); } catch(e){} }
  function djb2(s){ var h = 5381; for (var i=0;i<s.length;i++){ h = ((h<<5)+h + s.charCodeAt(i))|0; } return (h>>>0).toString(16); }

  var tries = 0;
  (function attach(){
    var drawer = document.querySelector('.memo-drawer');
    var pad = drawer && drawer.querySelector('.memo-pad');
    var statusRow = drawer && drawer.querySelector('.memo-status');
    if(!drawer || !pad || !statusRow){
      if(tries++ < 20){ setTimeout(attach, 200); }
      return;
    }
    if(drawer.querySelector('.qa-gen-bar')) return; // idempotent

    var bar = document.createElement('div');
    bar.className = 'qa-gen-bar';
    bar.innerHTML =
      '<button class="qa-gen-btn" type="button"><span class="qa-spin"></span><span class="qa-label">🤖 Q&amp;A 생성</span></button>' +
      '<div class="qa-gen-status" aria-live="polite"></div>';
    statusRow.insertAdjacentElement('afterend', bar);

    var btn = bar.querySelector('.qa-gen-btn');
    var label = bar.querySelector('.qa-label');
    var status = bar.querySelector('.qa-gen-status');

    function setStatus(html, cls){ status.className = 'qa-gen-status' + (cls ? ' ' + cls : ''); status.innerHTML = html; }
    function busy(on){ btn.disabled = on; btn.classList.toggle('busy', on); label.textContent = on ? '생성 중…' : '🤖 Q&A 생성'; }
    function runningText(t){ return '⏳ Q&amp;A 생성 중… ' + t + ' 경과. 브릿지에서 계속 진행 중이며, 탭을 닫았다 열어도 다시 이어집니다.'; }

    function handle(res){
      var st = res && res.status;
      var ph = ''; try { ph = localStorage.getItem(PHKEY) || ''; } catch(e){}
      function seal(){ if(ph) hset(ph); try { localStorage.removeItem(PHKEY); } catch(e){} }
      if(st === 'ok'){
        var deferred = (res.deferred|0);
        if(!deferred) seal();   /* 남긴 질문이 있으면 클라이언트 해시도 봉인하지 않는다(재클릭 = 이어받기) */
        var cards = (res.new_cards && res.new_cards.length) || (res.new_qids && res.new_qids.length) || 0;
        var qn = (res.new_questions && res.new_questions.length) || cards;
        var msg = '✅ 메모 질문 ' + qn + '개를 카드 ' + cards + '장으로 ⑥ Q&amp;A 탭에 추가했습니다.';
        if(deferred) msg += ' 남은 질문 ' + deferred + '개는 버튼을 다시 눌러 이어서 생성할 수 있습니다.';
        setStatus(msg + ' <button class="qa-link" data-reload>새로고침하여 보기</button>', 'ok');
      }
      else if(st === 'noop'){
        /* 서버는 processed_hash 를 봉인하지 않는다(noop_hash 만 기록). 오판 대비 우회를 항상 노출. */
        setStatus('새로 추출된 질문이 없습니다. (메모에 새 질문이 없거나 이미 반영됨) <button class="qa-link" data-force>그래도 다시 생성</button>');
      }
      else if(st === 'nochange'){
        if(res.reason === 'noop'){
          setStatus('새 질문이 없다고 판정된 메모입니다. <button class="qa-link" data-force>그래도 다시 생성</button>');
        } else {
          seal();
          setStatus('메모 변경 없음 - 새로 추가할 질문이 없습니다. <button class="qa-link" data-force>그래도 다시 생성</button>');
        }
      }
      else if(st === 'busy'){ setStatus(res.message || '이미 생성 중입니다. 잠시 후 다시 시도하세요.', 'err'); }
      else if(st === 'empty'){ setStatus(res.message || '메모를 먼저 작성하세요.', 'err'); }
      else { setStatus('⚠ ' + ((res && res.message) || '생성 실패'), 'err'); }
    }

    function jobOpts(force, resumeOnly, memo){
      return {
        path: '/gen-qa',
        body: {short: SHORT, memo: memo || '', force: !!force},
        jobKey: JOBKEY,
        resumeOnly: !!resumeOnly,
        running: runningText,
        onStatus: function(h, c){ setStatus(h, c); },
        onResult: function(res){ busy(false); handle(res); },
        onGiveUp: function(){
          busy(false);
          setStatus('⌛ 오래 기다렸지만 아직 결과가 오지 않았습니다. <b>서버 작업은 계속 진행 중일 수 있습니다</b> - 브릿지 콘솔 로그를 확인하세요. 이 페이지를 새로고침하면 진행 중인 작업에 다시 연결됩니다.', 'err');
        },
        onLost: function(){ busy(false); setStatus('진행 중이던 작업을 서버에서 찾지 못했습니다 (브릿지 재시작). 다시 시도하세요.', 'err'); },
        onError: function(err){
          busy(false);
          if(err && err.name === 'AbortError'){
            setStatus('⚠ 접수 응답이 20초 안에 오지 않았습니다. 브릿지가 <b>구버전</b>이면 비동기 접수를 지원하지 않습니다 - 브릿지를 재시작한 뒤 다시 시도하세요.', 'err');
          } else {
            setStatus('⚠ 요청을 보내지 못했습니다. 브릿지 콘솔 로그를 확인하세요.', 'err');
          }
        }
      };
    }

    function run(force){
      var memo = pad.value.trim();
      if(!memo){ setStatus('메모를 먼저 작성하세요.', 'err'); return; }
      var curHash = djb2(memo);
      if(!force && curHash === hget()){
        setStatus('이미 이 메모로 생성했습니다. <button class="qa-link" data-force>그래도 다시 생성</button>');
        return;
      }
      try { localStorage.setItem(MEMOKEY, pad.value); localStorage.setItem(PHKEY, curHash); } catch(e){}  /* 내용 무손실 */

      busy(true);
      setStatus('브릿지 서버 확인 중…');
      window.__qaBridgeEnsure(function(up){
        if(!up){
          setStatus('⚠ 브릿지를 켜지 못했습니다. 최초 1회 설정이 필요할 수 있어요 - 터미널에서 <code>python tools/qa_bridge_register.py</code> 실행(자동 시작 등록), 또는 <code>python tools/qa_bridge.py</code> 직접 실행.', 'err');
          busy(false); return;
        }
        setStatus(runningText('0초'));
        window.__qaBridgeJob2(jobOpts(force, false, memo));
      }, function(msg){ setStatus(msg); });
    }

    /* 새로고침·재오픈 시: 진행 중이던 job 이 있으면 그 job 에 다시 붙는다 (중복 실행 방지의 핵심) */
    (function resume(){
      busy(true);
      if(!window.__qaBridgeJob2(jobOpts(false, true, ''))){ busy(false); }
    })();

    btn.addEventListener('click', function(){ run(false); });
    status.addEventListener('click', function(e){
      var f = e.target.closest('[data-force]');
      var r = e.target.closest('[data-reload]');
      if(f){ e.preventDefault(); run(true); }
      else if(r){ e.preventDefault(); try { localStorage.setItem(MEMOKEY, pad.value); } catch(err){} location.reload(); }
    });
  })();
})();
</script>
"""


import re

# 이전 주입 블록(v1/v2)을 헤더 주석으로 식별해 제거 → 재주입 = 업데이트.
# 닫는 태그 뒤 인접 공백(\s*)까지 소비해 재주입과 대칭 = 멱등(재실행 시 빈 줄 누적 없음).
_STRIP_CSS = re.compile(r"<style>\s*/\* ==== 메모 Q&A 생성 버튼 \(qa_button_inject\.py\).*?</style>\s*", re.S)
_STRIP_JS = re.compile(r"<script>\s*/\* ==== 메모 Q&A 생성 버튼 \(qa_button_inject\.py\).*?</script>\s*", re.S)


def inject_one(html_path):
    short = html_path.name.replace("_output.html", "")
    text = html_path.read_text(encoding="utf-8")

    if text.count("</body>") != 1:
        print(f"[FAIL] {html_path.name}: expected exactly 1 </body>")
        return False
    if "memo-fab" not in text:
        print(f"[FAIL] {html_path.name}: memo-fab missing (메모 기능 없음 - 먼저 memo 주입 필요)")
        return False
    if "--accent" not in text:
        print(f"[FAIL] {html_path.name}: --accent CSS var missing (not v4?)")
        return False

    had = "qa-gen-bar" in text
    text = _STRIP_CSS.sub("", text)
    text = _STRIP_JS.sub("", text)

    block = "<style>" + QA_CSS + "</style>\n" + QA_JS.replace("__SHORT__", short)
    text = text.replace("</body>", block + "\n</body>", 1)
    html_path.write_text(text, encoding="utf-8")

    check = html_path.read_text(encoding="utf-8")
    assert ".qa-gen-bar{" in check, "qa CSS not injected"
    assert 'var SHORT = "' + short + '"' in check, "qa JS SHORT not injected"
    assert ".qa-mem-root{" in check, "qa-mem card CSS not injected"
    assert ".qa-mem-cat," in check, "qa-mem helper CSS not injected (v4)"
    assert "__qaBridgeEnsure" in check, "auto-start helper not injected"
    assert "__qaBridgeJob2" in check, "job polling helper not injected (v2)"
    assert check.count("<script>\n/* ==== 메모 Q&A 생성 버튼") == 1, "duplicate qa block"
    print(f"[{'UPD' if had else 'OK '}]  {html_path.name}: Q&A 버튼 {'업데이트' if had else '주입'} (SHORT={short})")
    return True


def main():
    # Windows 콘솔(cp949)에서 한글·em-dash 출력이 죽지 않도록
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    args = sys.argv[1:]
    if not args:
        raise SystemExit('usage: python tools/qa_button_inject.py "papers/N. shortname" | --all')
    if args[0] == "--all":
        base = ROOT / "papers"
        htmls = sorted(base.glob("*/*_output.html"))
        if not htmls:
            raise SystemExit(f"[FAIL] no *_output.html under {base}")
        done = 0
        for h in htmls:
            if inject_one(h):
                done += 1
        print(f"\n총 {len(htmls)}편 중 {done}편 주입 (나머지는 이미 있음/skip).")
        return
    folder = Path(args[0])
    if not folder.is_absolute():
        folder = ROOT / folder
    htmls = list(folder.glob("*_output.html"))
    if len(htmls) != 1:
        raise SystemExit(f"[FAIL] expected 1 *_output.html in {folder}, found {len(htmls)}")
    inject_one(htmls[0])


if __name__ == "__main__":
    main()
