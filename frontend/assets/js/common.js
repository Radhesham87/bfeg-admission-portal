/* shared helpers for both panels */
function api(path) { return (window.API_BASE || "").replace(/\/$/, "") + path; }

let _toastTimer;
function toast(msg, bad) {
  let t = document.querySelector(".toast");
  if (!t) { t = document.createElement("div"); t.className = "toast"; document.body.appendChild(t); }
  t.textContent = msg;
  t.className = "toast show" + (bad ? " bad" : "");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { t.className = "toast"; }, 3000);
}

function esc(v) {
  return String(v == null ? "" : v)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Build one form control from a schema field. */
function fieldHtml(f) {
  const cls = "f" + (f.w === 3 ? " w3" : f.w === 2 ? " w2" : "");
  const req = f.req ? ' <span class="req">*</span>' : "";
  const hint = f.hint ? ` <span class="hint">${esc(f.hint)}</span>` : "";
  let ctrl;
  if (f.t === "sel") {
    ctrl = `<select id="${f.k}" data-key="${f.k}"><option value="">— select —</option>` +
           f.o.map(o => `<option>${esc(o)}</option>`).join("") + `</select>`;
  } else if (f.t === "area") {
    ctrl = `<textarea id="${f.k}" data-key="${f.k}"></textarea>`;
  } else {
    ctrl = `<input type="${f.t || "text"}" id="${f.k}" data-key="${f.k}">`;
  }
  return `<div class="${cls}"><label for="${f.k}">${esc(f.l)}${req}${hint}</label>${ctrl}</div>`;
}
