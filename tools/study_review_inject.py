# -*- coding: utf-8 -*-
"""study_review_inject.py - Paper Study 탭에 '검토 결과 파악하기' 버튼 + 피드백 패널 주입.

학습자가 Paper Study 에 쓴 답변(.study-write[data-skey])을 브릿지(tools/qa_bridge.py
`POST /review-study`)로 보내, study.json 기준 분석과 대조한 **단계별 피드백**을 그 탭
위 패널에 렌더한다(정합도 meter · 맞게 본 지점 · 잘못 본 관점+근거 · 놓친 논점 · 총평).
약한 부분은 브릿지가 ⑥ Q&A 탭에 '보완 학습' 카드로 보충한다.

- 버튼: `.study-toolbar-btns` 맨 앞에 `#study-review-btn`.
- 패널: `.study-toolbar` 바로 뒤에 `#study-review-panel`.
- 피드백은 `prstudy:{SHORT}:study_review` localStorage 에 저장 → 재오픈 시 복원.
- 근거 칩(.ev-chip[data-ev])은 이 논문의 기존 핸들러가 **초기 바인딩**이라 동적 칩엔 안 붙으므로,
  주입기가 패널 스코프 자체 점프 핸들러를 단다(getElementById → .sent[data-pair], 탭 이동+flash).
- 우아한 실패: 브릿지 꺼짐이면 /ping 실패를 잡아 안내.
- 비동기 job 폴링(v2, 2026-09-10): 요청에 `async:1` → 202 + job_id → `GET /job?id=` 를
  2.5초 간격 폴링(개별 fetch 10초, 상한 40분). job_id 는 `prstudy:{SHORT}:study_review_job`
  에 저장돼 새로고침·재오픈 후에도 진행 중인 검토에 다시 붙는다(중복 실행 방지).

additive · idempotent. #tab-study + .study-write 가 있는 논문 대상.
사용법:  python tools/study_review_inject.py "samples/cares"   |   --all
정본: samples/cares (모체는 papers/26. cares, 2026-07-09) · v2 비동기 job (2026-09-10).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SR_CSS = """
/* ==== Paper Study 검토 피드백 (study_review_inject.py) v2 ==== */
.study-btn.sr-review-btn{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:800}
.study-btn.sr-review-btn:hover{filter:brightness(1.06)}
.study-btn.sr-review-btn:disabled{opacity:.55;cursor:default}
#study-review-panel{margin:0 0 18px;border:1px solid var(--line);border-radius:14px;background:var(--paper);padding:16px 18px;box-shadow:var(--shadow)}
#study-review-panel[hidden]{display:none}
.sr-head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
.sr-head h3{margin:0;font-size:15px;font-weight:800;color:var(--accent)}
.sr-close{border:1px solid var(--line);background:#fff;border-radius:50%;width:26px;height:26px;font-size:15px;line-height:1;color:var(--muted);cursor:pointer}
.sr-status{font-size:12px;line-height:1.6;color:var(--muted);min-height:1.1em}
.sr-status.err{color:var(--rose)}.sr-status.ok{color:var(--mint)}
.sr-spin{width:13px;height:13px;border:2px solid var(--accent-pale);border-top-color:var(--accent);border-radius:50%;display:inline-block;vertical-align:-2px;margin-right:6px;animation:sr-spin .8s linear infinite}
@keyframes sr-spin{to{transform:rotate(360deg)}}
.sr-step{border-top:1px solid var(--line);padding:12px 0}
.sr-step:first-of-type{border-top:none}
.sr-step-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.sr-step-label{font-size:13.5px;font-weight:800;color:var(--ink)}
.sr-meter{flex:1;min-width:120px;height:8px;background:var(--accent-soft);border-radius:99px;overflow:hidden}
.sr-meter-fill{height:100%;background:var(--accent-mid)}
.sr-meter-fill.lo{background:var(--rose)}.sr-meter-fill.mid{background:var(--amber)}.sr-meter-fill.hi{background:var(--mint)}
.sr-match{font-size:12px;font-weight:800;color:var(--ink-soft);min-width:52px;text-align:right}
.sr-block{margin:8px 0 0}
.sr-block h5{margin:0 0 3px;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.sr-block ul{margin:0;padding-left:16px}
.sr-block li{font-size:13px;line-height:1.65;color:var(--ink);margin:2px 0}
.sr-why{color:var(--ink-soft);font-size:12.5px}
.sr-verdict{margin-top:8px;font-size:13px;line-height:1.65;color:var(--ink);background:var(--accent-soft);border-radius:8px;padding:8px 11px}
.sr-evs{display:inline-flex;gap:5px;flex-wrap:wrap;margin-left:6px;vertical-align:middle}
.sr-supp{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px;font-size:12.5px;color:var(--ink)}
.sr-supp .qa-link{color:var(--accent);font:inherit;font-size:12.5px;font-weight:700;background:none;border:none;padding:0;cursor:pointer;text-decoration:underline}
@media print{.sr-review-btn{display:none !important}}
"""

SR_JS = r"""
<script>
/* ==== Paper Study 검토 피드백 (study_review_inject.py) v2 - 브릿지 /review-study 비동기 job 폴링 ==== */
(function(){
  var SHORT = "__SHORT__";
  function bridgeUrl(){ try { return localStorage.getItem("prstudy:qa_bridge_url") || "http://127.0.0.1:8787"; } catch(e){ return "http://127.0.0.1:8787"; } }
  function fetchT(url, opts, ms){ var c = new AbortController(); var t = setTimeout(function(){ c.abort(); }, ms); opts = opts||{}; opts.signal = c.signal; return fetch(url, opts).finally(function(){ clearTimeout(t); }); }
  /* 공용: 브릿지 확인 + 꺼져 있으면 qabridge:// 로 자동 시작 후 대기 (qa_button_inject 와 공유) */
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

  var RKEY = "prstudy:" + SHORT + ":study_review";
  var JOBKEY = "prstudy:" + SHORT + ":study_review_job";   /* 진행 중 job_id - 새로고침 후 재접속용 */
  function rget(){ try { return localStorage.getItem(RKEY) || ""; } catch(e){ return ""; } }
  function rset(v){ try { localStorage.setItem(RKEY, v); } catch(e){} }
  function esc(s){ return String(s==null?"":s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

  var tries = 0;
  (function attach(){
    var pane = document.getElementById('tab-study');
    var btns = pane && pane.querySelector('.study-toolbar-btns');
    var toolbar = pane && pane.querySelector('.study-toolbar');
    if(!pane || !btns || !toolbar){ if(tries++ < 20){ setTimeout(attach, 200); } return; }
    if(pane.querySelector('#study-review-btn')) return; // idempotent

    var btn = document.createElement('button');
    btn.className = 'study-btn sr-review-btn';
    btn.id = 'study-review-btn';
    btn.type = 'button';
    btn.textContent = '검토 결과 파악하기';
    btns.insertBefore(btn, btns.firstChild);

    var panel = document.createElement('div');
    panel.id = 'study-review-panel';
    panel.hidden = true;
    panel.innerHTML =
      '<div class="sr-head"><h3>검토 결과 - 내 답변 vs Claude 기준 분석</h3>' +
      '<button class="sr-close" type="button" aria-label="닫기">×</button></div>' +
      '<div class="sr-status" aria-live="polite"></div><div class="sr-body"></div>';
    toolbar.insertAdjacentElement('afterend', panel);
    var statusEl = panel.querySelector('.sr-status');
    var bodyEl = panel.querySelector('.sr-body');
    panel.querySelector('.sr-close').addEventListener('click', function(){ panel.hidden = true; });

    function setStatus(html, cls){ statusEl.className = 'sr-status' + (cls?(' '+cls):''); statusEl.innerHTML = html; }
    function runningText(t){ return '<span class="sr-spin"></span>답변을 기준 분석과 대조 중… ' + t + ' 경과. 브릿지에서 계속 진행 중이며, 탭을 닫았다 열어도 다시 이어집니다.'; }

    function collectAnswers(){
      var out = {};
      pane.querySelectorAll('.study-write[data-skey]').forEach(function(ta){
        var k = ta.dataset.skey;
        if(k.indexOf(',') !== -1) return;      // 잠금 게이트용 합성 skey 제외
        var v = (ta.value||'').trim();
        if(v) out[k] = v;
      });
      return out;
    }

    function evChips(evs){
      if(!evs || !evs.length) return '';
      var chips = evs.map(function(e){ return '<button class="ev-chip" type="button" data-ev="'+esc(e.ref)+'">'+esc(e.label||e.ref)+'</button>'; }).join('');
      return '<span class="sr-evs">'+chips+'</span>';
    }

    function render(res){
      if(!res || !res.feedback){ bodyEl.innerHTML = ''; return; }
      var html = '';
      res.feedback.forEach(function(f){
        var m = Math.max(0, Math.min(100, parseInt(f.match,10)||0));
        var cls = m < 50 ? 'lo' : (m < 75 ? 'mid' : 'hi');
        html += '<div class="sr-step">';
        html += '<div class="sr-step-head"><span class="sr-step-label">'+esc(f.label||f.skey)+'</span>' +
                '<span class="sr-meter"><span class="sr-meter-fill '+cls+'" style="width:'+m+'%"></span></span>' +
                '<span class="sr-match">정합도 '+m+'</span></div>';
        if(f.aligned && f.aligned.length){
          html += '<div class="sr-block"><h5>맞게 파악한 지점</h5><ul>' +
                  f.aligned.map(function(x){ return '<li>'+esc(x)+'</li>'; }).join('') + '</ul></div>';
        }
        if(f.misread && f.misread.length){
          html += '<div class="sr-block"><h5>잘못 본 관점</h5><ul>' +
                  f.misread.map(function(x){
                    var t = typeof x === 'string' ? {point:x} : x;
                    return '<li>'+esc(t.point)+(t.why?(' <span class="sr-why">- '+esc(t.why)+'</span>'):'')+evChips(t.evidence)+'</li>';
                  }).join('') + '</ul></div>';
        }
        if(f.missing && f.missing.length){
          html += '<div class="sr-block"><h5>다루지 않은 논점</h5><ul>' +
                  f.missing.map(function(x){ return '<li>'+esc(x)+'</li>'; }).join('') + '</ul></div>';
        }
        if(f.verdict){ html += '<div class="sr-verdict">'+esc(f.verdict)+'</div>'; }
        html += '</div>';
      });
      if(res.qa_added && res.qa_added > 0){
        html += '<div class="sr-supp">약했던 '+res.qa_added+'개 논점을 ⑥ Q&amp;A 탭에 <strong>보완 학습</strong>으로 추가했습니다. ' +
                '<button class="qa-link" data-reload>새로고침하여 보기</button></div>';
      }
      bodyEl.innerHTML = html;
    }

    function handle(res){
      var st = res && res.status;
      if(st === 'ok'){
        rset(JSON.stringify(res)); render(res);
        var n = (res.feedback||[]).length;
        setStatus('✅ '+n+'개 단계 검토 완료' + (res.qa_added?(' · 보완 학습 '+res.qa_added+'개 추가'):''), 'ok');
      }
      else if(st === 'empty'){ setStatus(res.message || '작성된 답변이 없습니다.', 'err'); bodyEl.innerHTML=''; }
      else if(st === 'busy'){ setStatus(res.message || '이미 처리 중입니다.', 'err'); }
      else { setStatus('⚠ ' + ((res && res.message) || '검토 실패'), 'err'); }
    }

    function jobOpts(answers, resumeOnly){
      return {
        path: '/review-study',
        body: {short: SHORT, answers: answers || {}},
        jobKey: JOBKEY,
        resumeOnly: !!resumeOnly,
        running: runningText,
        onStatus: function(h, c){ setStatus(h, c); },
        onResult: function(res){ btn.disabled = false; handle(res); },
        onGiveUp: function(){
          btn.disabled = false;
          setStatus('⌛ 오래 기다렸지만 아직 결과가 오지 않았습니다. <b>서버 작업은 계속 진행 중일 수 있습니다</b> - 브릿지 콘솔 로그를 확인하세요. 이 페이지를 새로고침하면 진행 중인 작업에 다시 연결됩니다.', 'err');
        },
        onLost: function(){ btn.disabled = false; setStatus('진행 중이던 검토를 서버에서 찾지 못했습니다 (브릿지 재시작). 다시 시도하세요.', 'err'); },
        onError: function(err){
          btn.disabled = false;
          if(err && err.name === 'AbortError'){
            setStatus('⚠ 접수 응답이 20초 안에 오지 않았습니다. 브릿지가 <b>구버전</b>이면 비동기 접수를 지원하지 않습니다 - 브릿지를 재시작한 뒤 다시 시도하세요.', 'err');
          } else {
            setStatus('⚠ 요청을 보내지 못했습니다. 브릿지 콘솔 로그를 확인하세요.', 'err');
          }
        }
      };
    }

    // 저장된 피드백 복원
    (function(){ var v = rget(); if(v){ try { var res = JSON.parse(v); render(res); panel.hidden = false; setStatus('저장된 검토 결과입니다. 답변을 고친 뒤 다시 검토할 수 있습니다.'); } catch(e){} } })();

    /* 새로고침·재오픈 시: 진행 중이던 검토 job 이 있으면 다시 붙는다 */
    (function resume(){
      btn.disabled = true;
      if(window.__qaBridgeJob2(jobOpts(null, true))){ panel.hidden = false; }
      else { btn.disabled = false; }
    })();

    btn.addEventListener('click', function(){
      var answers = collectAnswers();
      panel.hidden = false;
      if(!Object.keys(answers).length){ setStatus('먼저 Paper Study 답변(연구질문·Gap·방법론·결론 등)을 작성하세요.', 'err'); bodyEl.innerHTML=''; return; }
      btn.disabled = true;
      setStatus('<span class="sr-spin"></span>브릿지 서버 확인 중…');
      window.__qaBridgeEnsure(function(up){
        if(!up){
          setStatus('⚠ 브릿지를 켜지 못했습니다. 최초 1회 설정이 필요할 수 있어요 - 터미널에서 <code>python tools/qa_bridge_register.py</code> 실행(자동 시작 등록), 또는 <code>python tools/qa_bridge.py</code> 직접 실행.', 'err');
          btn.disabled = false; return;
        }
        setStatus(runningText('0초'));
        window.__qaBridgeJob2(jobOpts(answers, false));
      }, function(msg){ setStatus(msg); });
    });

    // 패널 스코프 근거 점프 + 새로고침 (동적 칩은 기존 핸들러가 안 잡으므로 자체 처리)
    function flashEl(el, isSent){
      if(isSent){
        var tw = document.querySelectorAll('.sent[data-pair="'+el+'"]');
        tw.forEach(function(s){ s.classList.add('ev-hl','ev-sent-flash'); });
        setTimeout(function(){ tw.forEach(function(s){ s.classList.remove('ev-hl','ev-sent-flash'); }); }, 3600);
      } else {
        var t = el.querySelector('.section-header') || el;
        t.classList.add('flash-target','ev-flash');
        setTimeout(function(){ t.classList.remove('flash-target','ev-flash'); }, 2000);
      }
    }
    function navTo(tab){ var b = document.querySelector('.tab-btn[data-tab="'+tab+'"]'); if(b) b.click(); }
    function jump(ref){
      var el = document.getElementById(ref);
      var isSent = false;
      if(!el){ el = document.querySelector('#tab-reading .sent[data-pair="'+ref+'"]'); isSent = !!el; }
      if(!el) return;
      navTo('tab-reading');
      setTimeout(function(){ el.scrollIntoView({behavior:'smooth', block: isSent?'center':'start'}); flashEl(isSent?ref:el, isSent); }, 120);
    }
    panel.addEventListener('click', function(e){
      var chip = e.target.closest('.ev-chip');
      if(chip && chip.dataset.ev){ e.preventDefault(); jump(chip.dataset.ev); return; }
      if(e.target.closest('[data-reload]')){ e.preventDefault(); location.reload(); }
    });
  })();
})();
</script>
"""


import re

# 닫는 태그 뒤 인접 공백(\s*)까지 소비해 재주입과 대칭 = 멱등(재실행 시 빈 줄 누적 없음).
_STRIP_CSS = re.compile(r"<style>\s*/\* ==== Paper Study 검토 피드백 \(study_review_inject\.py\).*?</style>\s*", re.S)
_STRIP_JS = re.compile(r"<script>\s*/\* ==== Paper Study 검토 피드백 \(study_review_inject\.py\).*?</script>\s*", re.S)


def inject_one(html_path):
    short = html_path.name.replace("_output.html", "")
    text = html_path.read_text(encoding="utf-8")
    if 'id="tab-study"' not in text:
        print(f"[FAIL] {html_path.name}: tab-study 없음")
        return False
    if "study-toolbar-btns" not in text:
        print(f"[FAIL] {html_path.name}: study-toolbar-btns 없음 (Study 셸만인 논문?)")
        return False
    if text.count("</body>") != 1:
        print(f"[FAIL] {html_path.name}: </body> 수 이상")
        return False

    had = "study-review-btn" in text
    text = _STRIP_CSS.sub("", text)
    text = _STRIP_JS.sub("", text)

    block = "<style>" + SR_CSS + "</style>\n" + SR_JS.replace("__SHORT__", short)
    text = text.replace("</body>", block + "\n</body>", 1)
    html_path.write_text(text, encoding="utf-8")
    chk = html_path.read_text(encoding="utf-8")
    assert "#study-review-panel{" in chk
    assert 'var SHORT = "' + short + '"' in chk
    assert "__qaBridgeEnsure" in chk
    assert "__qaBridgeJob2" in chk, "job polling helper not injected (v2)"
    assert chk.count("<script>\n/* ==== Paper Study 검토 피드백") == 1, "duplicate sr block"
    print(f"[{'UPD' if had else 'OK '}]  {html_path.name}: 검토 버튼 {'업데이트' if had else '주입'} (SHORT={short})")
    return True


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        raise SystemExit('usage: python tools/study_review_inject.py "papers/N. name" | --all')
    if args[0] == "--all":
        htmls = sorted((ROOT / "papers").glob("*/*_output.html"))
        done = 0
        for h in htmls:
            if inject_one(h):
                done += 1
        print(f"\n{len(htmls)}편 중 {done}편 주입.")
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
