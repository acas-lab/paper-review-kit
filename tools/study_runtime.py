# -*- coding: utf-8 -*-
"""study_inject.py 런타임 자산 — Paper Study 뷰어 마크업 + 자립형 JS.

CARES 정본과 동일한 클래스명(.para-reader/.pr-*/.asset-viewer/.av-*)을 쓰되,
CARES 모놀리식 IIFE에 의존하지 않는 자립형 IIFE. papers 1~3 DOM 규약에 배선:
  - 문장: [data-pair="pN_sM"]   - 섹션: section#sN
  - 단락: .paragraph-block#pN   - 자산: #fig_N (study_inject가 id 소급) 안의 img
탭 점프는 각 논문 nav 버튼 .click()으로 위임(해시 라우팅 재사용).
localStorage 네임스페이스 prstudy:{SHORT}:* — memo_inject.py의 메모와 공유(노트 내보내기 포함).
"""

# 뷰어 마크업 — av-guide(학습 가이드) 버튼은 papers 1~3에 study_modals 데이터가 없어 제외.
VIEWER_MARKUP = """
<div class="para-reader" role="dialog" aria-label="본문 단락 보기" aria-hidden="true">
  <div class="pr-panel">
    <div class="pr-head">
      <span class="pr-title"></span>
      <span class="pr-pos"></span>
      <button class="pr-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="pr-body"></div>
    <div class="pr-foot">
      <div class="pr-nav">
        <button class="pr-prev" type="button">‹ 이전 단락</button>
        <button class="pr-next" type="button">다음 단락 ›</button>
      </div>
      <span class="pr-hint">문장 클릭 = 형광펜</span>
      <button class="pr-open-translation" type="button">Translation 탭에서 이 단락 열기</button>
    </div>
  </div>
</div>
<div class="asset-viewer" role="dialog" aria-label="도표 상세 보기" aria-hidden="true">
  <div class="av-panel">
    <div class="av-head">
      <span class="av-label"></span>
      <span class="av-hint">이미지 클릭: 확대 · ESC/바깥 클릭: 닫기</span>
      <button class="av-close" type="button" aria-label="닫기">×</button>
    </div>
    <div class="av-body">
      <div class="av-img"><img src="" alt="" /></div>
      <div class="av-text">
        <div class="av-sec av-en"><h5>원문 캡션</h5><p></p></div>
        <div class="av-sec av-kr"><h5>번역</h5><p></p></div>
        <details class="av-interp"><summary>해석 보기</summary><div class="av-interp-body"></div></details>
      </div>
    </div>
  </div>
</div>
"""

RUNTIME_JS = r"""
<script>
/* ==== Paper Study 자립형 런타임 (study_inject.py) ==== */
(function(){
  var SHORT = "__SHORT__";
  var AV = __AV_JSON__;
  function K(k){ return "prstudy:" + SHORT + ":" + k; }
  function g(k){ try { return localStorage.getItem(K(k)) || ""; } catch(e){ return ""; } }
  function s(k,v){ try { localStorage.setItem(K(k), v); } catch(e){} }
  function del(k){ try { localStorage.removeItem(K(k)); } catch(e){} }
  function sg(k){ try { return sessionStorage.getItem(K(k)) || ""; } catch(e){ return ""; } }
  function ss(k,v){ try { sessionStorage.setItem(K(k), v); } catch(e){} }

  var pane = document.getElementById('tab-study');
  if(!pane) return;
  var reader = document.querySelector('.para-reader');
  var viewer = document.querySelector('.asset-viewer');

  function navClick(tab){ var b = document.querySelector('.tab-btn[data-tab="'+tab+'"]'); if(b) b.click(); }

  /* ---- 돌아가기 플로팅 버튼 ---- */
  var ret = document.createElement('button');
  ret.className = 'study-return'; ret.type = 'button';
  ret.textContent = '↩ Paper Study로 돌아가기';
  document.body.appendChild(ret);
  function showReturn(on){ ret.classList.toggle('visible', on); }
  ret.addEventListener('click', function(){ navClick('tab-study'); showReturn(false); });

  /* ---- 썸네일: Translation 자산에서 src 복사 + 클릭 시 도표 뷰어 ---- */
  pane.querySelectorAll('img[data-thumb-of]').forEach(function(im){
    var src = document.querySelector('#' + im.dataset.thumbOf + ' img');
    if(src && src.src) im.src = src.src;
    im.style.cursor = 'zoom-in';
    im.addEventListener('click', function(){ openViewer(im.dataset.thumbOf); });
  });

  /* ---- 서술칸 자동 저장 ---- */
  function paintWrite(ta){
    var wrap = ta.closest('.study-write-wrap');
    if(!wrap) return;
    var cnt = wrap.querySelector('.sw-count');
    if(cnt) cnt.textContent = ta.value.trim().length + '자';
  }
  pane.querySelectorAll('.study-write').forEach(function(ta){
    var key = ta.dataset.skey;
    ta.value = g(key);
    paintWrite(ta);
    var timer;
    ta.addEventListener('input', function(){
      paintWrite(ta);
      refreshReveals();
      clearTimeout(timer);
      timer = setTimeout(function(){
        s(key, ta.value);
        var wrap = ta.closest('.study-write-wrap');
        var sv = wrap && wrap.querySelector('.sw-saved');
        if(sv){ var d = new Date(); sv.textContent = '저장됨 ' + d.getHours() + ':' + ('0'+d.getMinutes()).slice(-2); }
      }, 400);
    });
  });

  /* ---- 잠금 토글 (내 답 min자 이상이면 활성) ---- */
  function revealLen(rev){
    var keys = rev.dataset.skey.split(',');
    var n = 0;
    keys.forEach(function(k){ n += g(k).trim().length; });
    // 아직 저장 전 입력도 반영
    keys.forEach(function(k){
      var ta = pane.querySelector('.study-write[data-skey="'+k+'"]');
      if(ta) n = Math.max(n, keys.reduce(function(a,kk){ var t=pane.querySelector('.study-write[data-skey="'+kk+'"]'); return a + (t? t.value.trim().length:0); },0));
    });
    return n;
  }
  function refreshReveals(){
    pane.querySelectorAll('.study-reveal').forEach(function(rev){
      var min = parseInt(rev.dataset.min || '0', 10);
      var btn = rev.querySelector('.study-reveal-btn');
      var claude = rev.querySelector('.study-claude');
      if(claude && !claude.hidden) return; // 이미 열림
      var ok = revealLen(rev) >= min;
      if(btn){ btn.disabled = !ok; var lock = btn.querySelector('.srb-lock'); if(lock) lock.style.display = ok ? 'none' : ''; }
    });
  }
  pane.querySelectorAll('.study-reveal').forEach(function(rev){
    var btn = rev.querySelector('.study-reveal-btn');
    var skip = rev.querySelector('.study-skip');
    var claude = rev.querySelector('.study-claude');
    function open(){ if(claude){ claude.hidden = false; } if(btn) btn.style.display='none'; if(skip) skip.style.display='none'; }
    if(btn) btn.addEventListener('click', function(){ if(!btn.disabled) open(); });
    if(skip) skip.addEventListener('click', open);
  });
  refreshReveals();

  /* ---- 체크박스 ---- */
  pane.querySelectorAll('.study-checkbox').forEach(function(cb){
    var key = 'ck:' + cb.dataset.ckey;
    if(g(key) === '1') cb.checked = true;
    cb.addEventListener('change', function(){ s(key, cb.checked ? '1' : '0'); });
  });

  /* ---- 근거 점프 (ev-chip) ---- */
  function flash(el){
    if(!el) return;
    el.classList.add('ev-flash');
    setTimeout(function(){ el.classList.remove('ev-flash'); }, 3600);
  }
  function jumpTo(ref){
    if(!ref) return;
    navClick('tab-reading');
    setTimeout(function(){
      var el = null;
      if(AV[ref]) el = document.getElementById(ref);                 // 자산
      else if(/^s\d+$/.test(ref)) el = document.getElementById(ref); // 섹션
      else if(/_s\d+$/.test(ref)) el = document.querySelector('[data-pair="'+ref+'"]'); // 문장
      else el = document.getElementById(ref);                        // 단락(.paragraph-block)
      if(el){
        el.scrollIntoView({behavior:'smooth', block:'center'});
        if(/_s\d+$/.test(ref)){ document.querySelectorAll('[data-pair="'+ref+'"]').forEach(function(x){ x.classList.add('ev-sent-flash'); setTimeout(function(){ x.classList.remove('ev-sent-flash'); },3600); }); }
        else flash(el);
      }
      showReturn(true);
    }, 60);
  }
  document.addEventListener('click', function(e){
    var chip = e.target.closest('.ev-chip');
    if(chip && chip.dataset.ev){ e.preventDefault(); jumpTo(chip.dataset.ev); }
  });

  /* ---- 본문 보기(플로팅 리더) ---- */
  var prBody = reader.querySelector('.pr-body');
  var prTitle = reader.querySelector('.pr-title');
  var prPos = reader.querySelector('.pr-pos');
  var curList = [], curIdx = 0;
  function markRead(pid){
    ss('read:'+pid, '1');
    document.querySelectorAll('.read-chip[data-read-pid="'+pid+'"]').forEach(function(c){ c.classList.add('read-done'); });
    refreshProgress();
  }
  function refreshProgress(){
    pane.querySelectorAll('.read-group').forEach(function(grp){
      var chips = grp.querySelectorAll('.read-chip');
      var done = 0; chips.forEach(function(c){ if(sg('read:'+c.dataset.readPid)==='1') done++; });
      var p = grp.querySelector('.read-progress'); if(p) p.textContent = done + '/' + chips.length;
    });
  }
  function renderReader(){
    var pid = curList[curIdx];
    prBody.innerHTML = '';
    var block = document.getElementById(pid);
    if(block && block.classList.contains('paragraph-block')){
      var clone = block.cloneNode(true);
      clone.removeAttribute('id');
      prBody.appendChild(clone);
    } else {
      prBody.textContent = '(단락을 찾을 수 없습니다: ' + pid + ')';
    }
    prPos.textContent = (curIdx+1) + ' / ' + curList.length;
    reader.querySelector('.pr-prev').disabled = curIdx <= 0;
    reader.querySelector('.pr-next').disabled = curIdx >= curList.length-1;
    reader.dataset.pid = pid;
    markRead(pid);
    applyHighlights(prBody);
  }
  function openReader(pid){
    // 같은 그룹의 단락들을 리스트로
    var group = null;
    pane.querySelectorAll('.read-group').forEach(function(grp){
      if(!group && grp.querySelector('.read-chip[data-read-pid="'+pid+'"]')) group = grp;
    });
    if(group){
      curList = Array.prototype.map.call(group.querySelectorAll('.read-chip'), function(c){ return c.dataset.readPid; });
      var g0 = group.querySelector('.read-group-label');
      prTitle.textContent = g0 ? g0.textContent : '본문 보기';
    } else {
      curList = [pid]; prTitle.textContent = '본문 보기';
    }
    curIdx = Math.max(0, curList.indexOf(pid));
    reader.classList.add('open');
    renderReader();
  }
  reader.querySelector('.pr-prev').addEventListener('click', function(){ if(curIdx>0){ curIdx--; renderReader(); } });
  reader.querySelector('.pr-next').addEventListener('click', function(){ if(curIdx<curList.length-1){ curIdx++; renderReader(); } });
  reader.querySelector('.pr-close').addEventListener('click', function(){ reader.classList.remove('open'); });
  reader.querySelector('.pr-open-translation').addEventListener('click', function(){ reader.classList.remove('open'); jumpTo(reader.dataset.pid); });
  reader.addEventListener('click', function(e){ if(e.target === reader) reader.classList.remove('open'); });
  document.addEventListener('click', function(e){
    var chip = e.target.closest('.read-chip, .view-chip');
    if(chip && chip.dataset.readPid){ e.preventDefault(); openReader(chip.dataset.readPid); }
  });

  /* ---- 도표 뷰어 ---- */
  var avImg = viewer.querySelector('.av-img img');
  var avLabel = viewer.querySelector('.av-label');
  var avEn = viewer.querySelector('.av-en p');
  var avKr = viewer.querySelector('.av-kr p');
  var avInterp = viewer.querySelector('.av-interp-body');
  var avInterpWrap = viewer.querySelector('.av-interp');
  function openViewer(aid){
    var d = AV[aid] || {};
    var src = document.querySelector('#' + aid + ' img');
    avImg.src = src ? src.src : '';
    avImg.alt = aid;
    avLabel.textContent = d.label || aid;
    avEn.textContent = d.en || '(원문 캡션 없음)';
    avKr.textContent = d.kr || '(번역 없음)';
    if(d.interp){ avInterp.innerHTML = d.interp; avInterpWrap.style.display=''; } else { avInterpWrap.style.display='none'; }
    viewer.classList.remove('av-tall','av-wide');
    viewer.classList.add('open');
    avImg.onload = function(){ viewer.classList.add(avImg.naturalWidth > avImg.naturalHeight*1.35 ? 'av-wide' : 'av-tall'); };
    if(avImg.complete && avImg.naturalWidth) avImg.onload();
  }
  viewer.querySelector('.av-close').addEventListener('click', function(){ viewer.classList.remove('open'); });
  viewer.addEventListener('click', function(e){ if(e.target === viewer) viewer.classList.remove('open'); });
  avImg.addEventListener('click', function(){ if(avImg.src){ window.open(avImg.src, '_blank'); } });

  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape'){
      if(viewer.classList.contains('open')) viewer.classList.remove('open');
      else if(reader.classList.contains('open')) reader.classList.remove('open');
    }
  });

  /* ---- 서론 goto 버튼 ---- */
  document.querySelectorAll('.study-goto').forEach(function(b){
    b.addEventListener('click', function(){ navClick('tab-study'); });
  });

  /* ---- 문장 형광펜 (Translation + 리더 클론, data-pair 동기) ---- */
  function applyHighlights(root){
    (root || document).querySelectorAll('.sent[data-pair]').forEach(function(sp){
      if(g('hl:'+sp.dataset.pair) === '1') sp.classList.add('user-hl');
    });
  }
  document.addEventListener('click', function(e){
    var sp = e.target.closest('.sent[data-pair]');
    if(!sp) return;
    if(!e.target.closest('#tab-reading') && !e.target.closest('.para-reader')) return;
    var pair = sp.dataset.pair;
    var on = g('hl:'+pair) !== '1';
    if(on) s('hl:'+pair,'1'); else del('hl:'+pair);
    document.querySelectorAll('.sent[data-pair="'+pair+'"]').forEach(function(x){ x.classList.toggle('user-hl', on); });
  });
  applyHighlights(document);

  /* ---- verdict mirror — 내 Step5 결론 반영 ---- */
  pane.querySelectorAll('[data-mirror]').forEach(function(m){
    var det = m.closest('.verdict-details');
    function fill(){ var v = g(m.dataset.mirror); m.textContent = v ? v : '(Step 5에서 결론을 먼저 작성하세요)'; }
    if(det) det.addEventListener('toggle', function(){ if(det.open) fill(); });
    fill();
  });

  /* ---- 노트 내보내기 / 가져오기 / 지우기 ---- */
  function collect(){
    var out = {}; var pre = 'prstudy:' + SHORT + ':';
    try {
      for(var i=0;i<localStorage.length;i++){ var k = localStorage.key(i); if(k && k.indexOf(pre)===0) out[k.slice(pre.length)] = localStorage.getItem(k); }
    } catch(e){}
    return out;
  }
  var exp = document.getElementById('study-export');
  if(exp) exp.addEventListener('click', function(){
    var data = collect();
    var payload = { short: SHORT, exportedAt: new Date().toISOString(), notes: data, memo: data['memo'] || '' };
    var blob = new Blob([JSON.stringify(payload, null, 2)], {type:'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    var d = new Date(); var ymd = ('' + d.getFullYear()).slice(2) + ('0'+(d.getMonth()+1)).slice(-2) + ('0'+d.getDate()).slice(-2);
    a.href = url; a.download = SHORT + '_study_notes_' + ymd + '.json';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    setTimeout(function(){ URL.revokeObjectURL(url); }, 1000);
  });
  var imp = document.getElementById('study-import');
  if(imp) imp.addEventListener('click', function(){
    var inp = document.createElement('input'); inp.type='file'; inp.accept='application/json';
    inp.addEventListener('change', function(){
      var f = inp.files[0]; if(!f) return;
      var r = new FileReader();
      r.onload = function(){
        try {
          var obj = JSON.parse(r.result);
          if(obj.short && obj.short !== SHORT && !confirm('다른 논문(' + obj.short + ')의 노트입니다. 그래도 가져올까요?')) return;
          var notes = obj.notes || {};
          Object.keys(notes).forEach(function(k){ s(k, notes[k]); });
          alert('가져왔습니다. 페이지를 새로고침합니다.'); location.reload();
        } catch(e){ alert('파일을 읽을 수 없습니다.'); }
      };
      r.readAsText(f);
    });
    inp.click();
  });
  var clr = document.getElementById('study-clear');
  if(clr) clr.addEventListener('click', function(){
    if(!confirm('이 논문의 모든 메모·형광펜·체크를 지웁니다. 계속할까요?')) return;
    var pre = 'prstudy:' + SHORT + ':'; var keys = [];
    try { for(var i=0;i<localStorage.length;i++){ var k = localStorage.key(i); if(k && k.indexOf(pre)===0) keys.push(k); } } catch(e){}
    keys.forEach(function(k){ try{ localStorage.removeItem(k); }catch(e){} });
    location.reload();
  });

  refreshProgress();
})();
</script>
"""
