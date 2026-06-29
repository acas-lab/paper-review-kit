// Paper Review 대시보드 — 프론트 로직 (의존성 없음)
const $ = (s) => document.querySelector(s);
const log = $("#log"), input = $("#input"), sendBtn = $("#send"), stopBtn = $("#stop");

let ws = null, busy = false, curAssistant = null, selectedPaper = null;
let imageMode = localStorage.getItem("imageMode") || "codex";  // 'codex' | 'claude_svg'
let codexAvailable = true;
let turnStart = 0, tickTimer = null, statusPhase = "";

/* ---------- 진행률/생존 표시 (중지 버튼 왼쪽) ---------- */
function fmtElapsed(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
}
function renderStatus() {
  const el = $("#status");
  if (!el) return;
  if (busy) {
    el.className = "status busy";
    el.innerHTML = '<span class="st-dot"></span><span class="st-text"></span><span class="st-time"></span>';
    el.querySelector(".st-text").textContent = statusPhase || "작업 중";
    el.querySelector(".st-time").textContent = turnStart ? fmtElapsed(Date.now() - turnStart) : "";
    el.title = "작동 중 — 시간이 흐르면 살아 있는 것입니다";
  } else {
    el.className = "status idle";
    el.innerHTML = '<span class="st-dot"></span><span class="st-text">대기</span>';
  }
}
function setPhase(p) { statusPhase = p; renderStatus(); }
function startTick() {
  turnStart = Date.now();
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = setInterval(renderStatus, 1000);  // ticking clock = proof it's alive
}
function stopTick() {
  if (tickTimer) { clearInterval(tickTimer); tickTimer = null; }
}

/* ---------- 이미지 생성 방식 토글 ---------- */
const MODE_NOTE = {
  codex: "codex CLI로 풀-블리드 일러스트 PNG를 생성합니다.",
  claude_svg: "Claude가 외부 도구 없이 인라인 SVG 도식을 직접 그립니다.",
};
function renderImgMode() {
  document.querySelectorAll("#imgmode .seg-btn").forEach((b) => {
    const on = b.dataset.mode === imageMode;
    b.classList.toggle("active", on);
    b.setAttribute("aria-checked", on ? "true" : "false");
  });
  const note = $("#imgmodeNote");
  if (!codexAvailable) {
    note.className = "seg-note locked";
    note.textContent = "codex CLI가 없어 'Claude 자체(SVG)'로 고정됩니다.";
  } else {
    note.className = "seg-note";
    note.textContent = MODE_NOTE[imageMode];
  }
}
function setImageMode(mode) {
  if (mode === "codex" && !codexAvailable) return;  // 잠김
  imageMode = mode;
  localStorage.setItem("imageMode", mode);
  renderImgMode();
}
document.querySelectorAll("#imgmode .seg-btn").forEach((b) => {
  b.addEventListener("click", () => setImageMode(b.dataset.mode));
});

/* ---------- 채팅 렌더 ---------- */
function scroll() { log.scrollTop = log.scrollHeight; }
function addMsg(cls, text) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.textContent = text;
  log.appendChild(d); scroll();
  return d;
}
function appendAssistant(text) {
  if (!curAssistant) { curAssistant = addMsg("assistant", ""); }
  curAssistant.textContent += text; scroll();
}
function addTool(name, brief) {
  const d = document.createElement("div");
  d.className = "tool";
  d.innerHTML = `🔧 <b></b> <span class="brief"></span>`;
  d.querySelector("b").textContent = name;
  d.querySelector(".brief").textContent = brief || "";
  log.appendChild(d); scroll();
}
function addResult(ev) {
  const d = document.createElement("div");
  d.className = "result-line" + (ev.is_error ? " err" : "");
  // 구독(OAuth) 실행이라 토큰 과금 없음 → 비용 대신 소요 시간 표시
  const ms = ev.duration_ms != null ? ev.duration_ms : (turnStart ? Date.now() - turnStart : 0);
  const took = ms ? ` · ${fmtElapsed(ms)} 소요` : "";
  d.textContent = ev.is_error ? "⚠ 오류로 종료" : `✓ 완료${took}`;
  log.appendChild(d); scroll();
}

/* ---------- WebSocket ---------- */
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    switch (ev.type) {
      case "ready": setBusy(false); break;
      case "text": appendAssistant(ev.text); setPhase("응답 작성 중"); break;
      case "tool_use": curAssistant = null; addTool(ev.name, ev.brief); setPhase("🔧 " + ev.name); break;
      case "tool_result": setPhase("도구 완료, 이어서 작업 중"); break;
      case "thinking": setPhase("생각 중"); break;
      case "summary": renderSummary(ev); break;
      case "result": curAssistant = null; addResult(ev); refreshPapers(); break;
      case "turn_end": setBusy(false); curAssistant = null; break;
      case "error": curAssistant = null; addMsg("system", "⚠ " + ev.message); setBusy(false); break;
    }
  };
  ws.onclose = () => { addMsg("system", "연결이 끊어졌어요. 새로고침하면 다시 연결됩니다."); setBusy(true); };
  ws.onerror = () => {};
}

function setBusy(b) {
  busy = b;
  sendBtn.disabled = b; stopBtn.disabled = !b;
  sendBtn.textContent = b ? "작업 중…" : "전송";
  if (b) { if (!turnStart) startTick(); } else { stopTick(); turnStart = 0; }
  renderStatus();
}

function send(textOverride) {
  const text = (textOverride != null ? textOverride : input.value).trim();
  if (!text || busy || !ws || ws.readyState !== 1) return;
  // 선택된 논문이 있으면 그 논문을 작업 대상으로 명시(Claude가 어느 논문을 고칠지 알도록)
  // 이미지 생성 모드도 항상 명시 — CLAUDE.md/§11.8 규약대로 Claude가 codex/SVG 중 택일
  const tags = `[이미지 생성 모드: ${imageMode}]`
    + (selectedPaper ? ` [작업 대상 논문: papers/${selectedPaper}]` : "");
  const payload = `${tags} ${text}`;
  addMsg("user", (selectedPaper ? `→ [${selectedPaper}] ` : "") + text);
  curAssistant = null;
  ws.send(JSON.stringify({ type: "user", text: payload }));
  if (textOverride == null) input.value = "";
  setPhase("요청 전송됨");
  setBusy(true);
}

/* ---------- 작업 대상 논문 (기존 HTML 수정) ---------- */
function selectPaper(folder) {
  selectedPaper = folder;
  $("#apName").textContent = folder;
  $("#activePaper").hidden = false;
  input.placeholder = `"${folder}" 수정 요청 (예: 이 번역 어색한 곳 고쳐줘 / fig_2 다시 잘라줘)`;
  input.focus();
}
function clearPaper() {
  selectedPaper = null;
  $("#activePaper").hidden = true;
  input.placeholder = "요청을 입력하세요 (Shift+Enter 줄바꿈, Enter 전송)";
}
$("#apClear").addEventListener("click", clearPaper);
$("#apRebuild").addEventListener("click", () => {
  if (!selectedPaper) return;
  send("이 논문 폴더의 `_build.py`를 실행해서 출력 HTML을 다시 빌드해줘. 수정한 JSON이 HTML에 반영되도록.");
});

$("#composer").addEventListener("submit", (e) => { e.preventDefault(); send(); });
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
stopBtn.addEventListener("click", () => {
  if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "interrupt" }));
});

/* ---------- 인증 상태 ---------- */
async function loadAuth() {
  try {
    const a = await (await fetch("/api/auth")).json();
    codexAvailable = !!a.codex_available;
    const codexBtn = document.querySelector('#imgmode .seg-btn[data-mode="codex"]');
    if (codexBtn) codexBtn.disabled = !codexAvailable;
    if (!codexAvailable) imageMode = "claude_svg";  // codex 없으면 자동 폴백
    renderImgMode();
    const el = $("#auth");
    if (!a.claude_logged_in) {
      el.className = "auth auth-warn";
      el.textContent = "⚠ Claude 로그인 필요 — 터미널에서 claude 로그인";
    } else if (a.api_key_set) {
      el.className = "auth auth-warn";
      el.textContent = "⚠ API 키가 설정됨 (구독 대신 키 과금)";
    } else {
      el.className = "auth auth-ok";
      el.textContent = "✓ Claude 구독 로그인됨" + (a.codex_available ? " · codex ✓" : " · codex 없음(이미지 스킵)");
    }
  } catch { $("#auth").textContent = "인증 상태 확인 실패"; }
}

/* ---------- 논문 목록 / 미리보기 ---------- */
async function refreshPapers() {
  try {
    const list = await (await fetch("/api/papers")).json();
    const ul = $("#papers"); ul.innerHTML = "";
    if (!list.length) { ul.innerHTML = '<li class="muted">아직 논문이 없어요.</li>'; return; }
    for (const p of list) {
      const li = document.createElement("li");
      const head = document.createElement("div");
      head.className = "paper-head";
      const name = document.createElement("span");
      name.className = "paper-name"; name.textContent = p.folder;
      const edit = document.createElement("button");
      edit.type = "button"; edit.className = "edit"; edit.textContent = "✎ 수정";
      edit.onclick = () => selectPaper(p.folder);
      head.appendChild(name); head.appendChild(edit);
      li.appendChild(head);
      for (const out of p.outputs) {
        const a = document.createElement("span");
        a.className = "out"; a.textContent = "▸ " + out + " (미리보기)";
        a.onclick = () => preview(p.folder, out);
        li.appendChild(a);
      }
      ul.appendChild(li);
    }
  } catch {}
}
function preview(folder, file) {
  const url = `/papers/${encodeURIComponent(folder)}/${encodeURIComponent(file)}`;
  $("#preview").src = url;
  const open = $("#openNew"); open.href = url; open.style.display = "inline-block";
}
$("#refresh").addEventListener("click", refreshPapers);

/* ---------- 업로드 ---------- */
const pdf = $("#pdf"), drop = $("#drop"), uploadMsg = $("#uploadMsg");
// NOTE: #drop is a <label> wrapping the hidden <input id="pdf">, so a click already
// opens the file dialog natively. Do NOT also call pdf.click() here — that fired the
// dialog a SECOND time. (bugfix: 파일 선택창이 두 번 뜨던 문제)
pdf.addEventListener("change", () => pdf.files[0] && upload(pdf.files[0]));
["dragover", "dragenter"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) upload(f); });

async function upload(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    uploadMsg.className = "upload-msg err"; uploadMsg.textContent = "PDF만 올릴 수 있어요."; return;
  }
  uploadMsg.className = "upload-msg"; uploadMsg.textContent = "업로드 중…";
  const fd = new FormData(); fd.append("file", file);
  try {
    const r = await fetch("/api/upload", { method: "POST", body: fd });
    const j = await r.json();
    if (j.error) { uploadMsg.className = "upload-msg err"; uploadMsg.textContent = j.error; return; }
    uploadMsg.className = "upload-msg"; uploadMsg.textContent = "✓ 저장됨: " + j.saved;
    $("#dropText").textContent = file.name;
    clearPaper();
    input.value = `방금 "${j.saved}" 를 올렸어. 이 논문으로 새 papers 폴더를 만들고 workflow.md 단계대로 6탭 학습 HTML을 만들어줘. 디자인·구성은 samples/free_example 정본을 따르고 ⑤⑥은 셸만.`;
    input.focus();
  } catch (e) {
    uploadMsg.className = "upload-msg err"; uploadMsg.textContent = "업로드 실패: " + e;
  }
}

/* ---------- 플로팅 논문 요약 (핵심 관찰 / 방법론) ---------- */
function fillRows(container, rows) {
  container.innerHTML = "";
  if (!rows || !rows.length) { container.innerHTML = '<p class="sum-empty">아직 생성 전…</p>'; return; }
  for (const r of rows) {
    const row = document.createElement("div"); row.className = "sum-row";
    const tag = document.createElement("span"); tag.className = "sum-tag"; tag.textContent = r.tag || "";
    const body = document.createElement("div"); body.className = "sum-rb"; body.innerHTML = r.body || "";
    if (r.tag) row.appendChild(tag);
    row.appendChild(body); container.appendChild(row);
  }
}
function renderSummary(ev) {
  fillRows($("#sumObserve"), ev.observe);
  fillRows($("#sumMethod"), ev.method);
  $("#sumPaper").textContent = ev.paper || "";
  const fab = $("#sumFab");
  if (fab.hidden) { fab.hidden = false; fab.classList.add("pulse"); setTimeout(() => fab.classList.remove("pulse"), 4000); }
}
function toggleSummary(force) {
  const panel = $("#sumPanel");
  const open = force != null ? force : panel.hidden;
  panel.hidden = !open;
  $("#sumFab").classList.toggle("active", open);
}
$("#sumFab").addEventListener("click", () => toggleSummary());
$("#sumClose").addEventListener("click", () => toggleSummary(false));

/* ---------- 시작 ---------- */
renderImgMode(); connect(); loadAuth(); refreshPapers();
setBusy(true);
