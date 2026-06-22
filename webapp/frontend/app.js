// Paper Review 대시보드 — 프론트 로직 (의존성 없음)
const $ = (s) => document.querySelector(s);
const log = $("#log"), input = $("#input"), sendBtn = $("#send"), stopBtn = $("#stop");

let ws = null, busy = false, curAssistant = null;

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
  const cost = ev.cost_usd != null ? ` · ${ev.cost_usd.toFixed(4)} USD 상당` : "";
  d.textContent = ev.is_error ? "⚠ 오류로 종료" : `✓ 완료${cost}`;
  log.appendChild(d); scroll();
}

/* ---------- WebSocket ---------- */
function connect() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    switch (ev.type) {
      case "ready": setBusy(false); break;
      case "text": appendAssistant(ev.text); break;
      case "tool_use": curAssistant = null; addTool(ev.name, ev.brief); break;
      case "tool_result": break;
      case "thinking": break;
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
}

function send() {
  const text = input.value.trim();
  if (!text || busy || !ws || ws.readyState !== 1) return;
  addMsg("user", text);
  curAssistant = null;
  ws.send(JSON.stringify({ type: "user", text }));
  input.value = ""; setBusy(true);
}

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
      li.textContent = p.folder;
      for (const out of p.outputs) {
        const a = document.createElement("span");
        a.className = "out"; a.textContent = "▸ " + out;
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
drop.addEventListener("click", () => pdf.click());
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
    input.value = `방금 "${j.saved}" 를 올렸어. 이 논문으로 새 papers 폴더를 만들고 workflow.md 10단계로 6탭 학습 HTML을 만들어줘. 디자인은 SGL 정본을 따르고 ⑤⑥은 셸만.`;
    input.focus();
  } catch (e) {
    uploadMsg.className = "upload-msg err"; uploadMsg.textContent = "업로드 실패: " + e;
  }
}

/* ---------- 시작 ---------- */
connect(); loadAuth(); refreshPapers();
setBusy(true);
