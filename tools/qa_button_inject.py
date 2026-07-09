# -*- coding: utf-8 -*-
"""qa_button_inject.py — 메모 플로팅 드로어에 'Q&A 생성' 버튼을 주입.

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

또한 ⑥ tab-qa 에 헤드리스 claude 가 써넣을 카드용 `.qa-mem-*` CSS 를 함께 주입한다
(스타일을 파일에 고정 → 헤드리스 런은 클래스만 맞추면 됨).

사용법:  python tools/qa_button_inject.py "papers/N. shortname"
        python tools/qa_button_inject.py --all        # papers 전체
검증  :  재실행 시 이미 있으면 skip (idempotent).

정본: papers 1~26 (2026-07-09).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

QA_CSS = """
/* ==== 메모 Q&A 생성 버튼 (qa_button_inject.py) ==== */
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
@media print{.qa-gen-bar{display:none !important}}
"""

QA_JS = r"""
<script>
/* ==== 메모 Q&A 생성 버튼 (qa_button_inject.py) — 로컬 브릿지 연동 + qabridge:// 자동 시작 ==== */
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

  var HKEY = "prstudy:" + SHORT + ":qa_client_hash";
  var MEMOKEY = "prstudy:" + SHORT + ":memo";
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

    function run(force){
      var memo = pad.value.trim();
      if(!memo){ setStatus('메모를 먼저 작성하세요.', 'err'); return; }
      var curHash = djb2(memo);
      if(!force && curHash === hget()){
        setStatus('이미 이 메모로 생성했습니다. <button class="qa-link" data-force>그래도 다시 생성</button>');
        return;
      }
      try { localStorage.setItem(MEMOKEY, pad.value); } catch(e){}  /* 내용 무손실 */

      busy(true);
      setStatus('브릿지 서버 확인 중…');
      window.__qaBridgeEnsure(function(up){
        if(!up){
          setStatus('⚠ 브릿지를 켜지 못했습니다. 최초 1회 설정이 필요할 수 있어요 — 터미널에서 <code>python tools/qa_bridge_register.py</code> 실행(자동 시작 등록), 또는 <code>python tools/qa_bridge.py</code> 직접 실행.', 'err');
          busy(false); return;
        }
        setStatus('Claude가 Q&A를 생성하는 중입니다. 완료될 때까지 이 브라우저 탭을 열어 두세요. (수십 초~몇 분 소요)');
        fetchT(bridgeUrl() + '/gen-qa', {
          method:'POST',
          headers:{'Content-Type':'text/plain;charset=UTF-8'},
          body: JSON.stringify({short: SHORT, memo: memo, force: !!force})
        }, 600000)
        .then(function(r){ return r.json(); })
        .then(function(res){
          var st = res.status;
          if(st === 'ok'){
            hset(curHash);
            var n = (res.new_qids && res.new_qids.length) || (res.new_questions && res.new_questions.length) || 0;
            setStatus('✅ 새 질문 ' + n + '개를 ⑥ Q&A 탭에 추가했습니다. <button class="qa-link" data-reload>새로고침하여 보기</button>', 'ok');
          } else if(st === 'noop'){ hset(curHash); setStatus('새로 추출된 질문이 없습니다. (메모에 새 질문이 없거나 이미 반영됨)'); }
          else if(st === 'nochange'){ hset(curHash); setStatus('메모 변경 없음 — 새로 추가할 질문이 없습니다.'); }
          else if(st === 'busy'){ setStatus(res.message || '이미 생성 중입니다. 잠시 후 다시 시도하세요.', 'err'); }
          else { setStatus('⚠ ' + (res.message || '생성 실패'), 'err'); }
        })
        .catch(function(err){
          if(err && err.name === 'AbortError') setStatus('⚠ 응답이 너무 오래 걸려 중단됐습니다. 브릿지 콘솔 로그를 확인하세요.', 'err');
          else setStatus('⚠ 생성 요청 중 오류가 발생했습니다. 브릿지 콘솔 로그를 확인하세요.', 'err');
        })
        .finally(function(){ busy(false); });
      }, function(msg){ setStatus(msg); });
    }

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
        print(f"[FAIL] {html_path.name}: memo-fab missing (메모 기능 없음 — 먼저 memo 주입 필요)")
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
    assert "__qaBridgeEnsure" in check, "auto-start helper not injected"
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
