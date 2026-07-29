/* ==========================================================
   ADMIN PANEL
   The session token lives in memory + sessionStorage, so it is
   gone when the tab closes. Every data route requires it.
   ========================================================== */

let TOKEN = sessionStorage.getItem("bfeg_token") || "";
let PAGE = 1, PER = 50, TOTAL = 0, SCHEMA = null;

function headers() {
  return { "Content-Type": "application/json", "Authorization": "Bearer " + TOKEN };
}

function showAdmin(on) {
  document.getElementById("loginView").style.display = on ? "none" : "";
  document.getElementById("adminView").style.display = on ? "" : "none";
  document.getElementById("signOutBtn").style.display = on ? "" : "none";
}

async function doLogin() {
  const btn = document.getElementById("loginBtn");
  const err = document.getElementById("loginErr");
  const username = document.getElementById("u").value.trim();
  const password = document.getElementById("p").value;
  err.textContent = "";

  if (!username || !password) { err.textContent = "Enter both username and password."; return; }

  btn.disabled = true; btn.textContent = "Signing in…";
  try {
    const res = await fetch(api("/api/admin/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const out = await res.json();
    if (!res.ok) throw new Error(out.detail || "Sign in failed");
    TOKEN = out.access_token;
    sessionStorage.setItem("bfeg_token", TOKEN);
    document.getElementById("p").value = "";
    showAdmin(true);
    await loadSchema();
    loadList(1);
  } catch (e) {
    err.textContent = e.message === "Failed to fetch"
      ? "Cannot reach the server. Check the API address in config.js."
      : e.message;
  } finally {
    btn.disabled = false; btn.textContent = "Sign in";
  }
}

function signOut() {
  TOKEN = "";
  sessionStorage.removeItem("bfeg_token");
  showAdmin(false);
  toast("Signed out.");
}

function handleAuthFailure(res) {
  if (res.status === 401 || res.status === 403) {
    signOut();
    document.getElementById("loginErr").textContent = "Session expired. Sign in again.";
    return true;
  }
  return false;
}

async function loadSchema() {
  try {
    const res = await fetch(api("/api/schema"));
    SCHEMA = await res.json();
  } catch (e) { SCHEMA = null; }
}

/* ---------------- list ---------------- */
async function loadList(page) {
  if (page < 1) return;
  PAGE = page;
  const q = document.getElementById("q").value.trim();
  const tbody = document.querySelector("#recs tbody");
  tbody.innerHTML = `<tr><td colspan="12" class="empty">Loading…</td></tr>`;

  try {
    const url = api(`/api/admin/submissions?page=${PAGE}&per_page=${PER}&q=${encodeURIComponent(q)}`);
    const res = await fetch(url, { headers: headers() });
    if (handleAuthFailure(res)) return;
    const out = await res.json();
    TOTAL = out.total;

    document.getElementById("count").textContent = `${TOTAL} application(s)`;
    const pages = Math.max(1, Math.ceil(TOTAL / PER));
    document.getElementById("pageInfo").textContent = `Page ${PAGE} of ${pages}`;
    document.getElementById("prev").disabled = PAGE <= 1;
    document.getElementById("next").disabled = PAGE >= pages;

    if (!out.items.length) {
      tbody.innerHTML = `<tr><td colspan="12" class="empty">No applications found.</td></tr>`;
      return;
    }
    tbody.innerHTML = out.items.map(r => `
      <tr>
        <td><span class="link" onclick="openDetail(${r.id})">${esc(r.reference)}</span></td>
        <td>${esc(r.full_name)}</td>
        <td>${esc(r.neet_roll)}</td>
        <td>${esc(r.cet_mobile)}</td>
        <td>${esc(r.district)}</td>
        <td>${esc(r.category)}</td>
        <td>${esc(r.quota)}</td>
        <td>${r.created_at ? new Date(r.created_at).toLocaleString("en-IN") : ""}</td>
        <td><span class="link" onclick="downloadPdf(${r.id})">PDF</span></td>
        <td><span class="link" onclick="downloadOne(${r.id})">Excel</span></td>
        <td><span class="link" onclick="openEdit(${r.id})">Edit</span></td>
        <td><span class="del" onclick="removeOne(${r.id},'${esc(r.full_name)}')">Delete</span></td>
      </tr>`).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="11" class="empty">Could not load applications.</td></tr>`;
  }
}

/* ---------------- detail ---------------- */
async function openDetail(id) {
  const res = await fetch(api(`/api/admin/submissions/${id}`), { headers: headers() });
  if (handleAuthFailure(res)) return;
  if (!res.ok) { toast("Could not open that application.", true); return; }
  const rec = await res.json();

  document.getElementById("dTitle").textContent = `${rec.full_name} — ${rec.reference}`;
  document.getElementById("dExcel").onclick = () => downloadOne(id);
  document.getElementById("dPdf").onclick = () => downloadPdf(id);
  document.getElementById("dEdit").onclick = () => { document.getElementById("detail").close(); openEdit(id); };

  let html = "";
  if (SCHEMA) {
    SCHEMA.sections.forEach(sec => {
      html += `<h4>${esc(sec.title)}</h4><table>`;
      sec.fields.forEach(f => {
        html += `<tr><td class="lab">${esc(f.l)}</td><td>${esc(rec.data[f.k] || "—")}</td></tr>`;
      });
      html += `</table>`;
    });
    const bcDocs = SCHEMA.barcode_documents || [];
    const mand = SCHEMA.mandatory_documents || [];
    const opt = SCHEMA.optional_documents || [];
    const mSt = SCHEMA.mandatory_status || ["Yes"];
    const oSt = SCHEMA.optional_status || ["Yes", "No"];

    const editRow = (d, n, statuses) => {
      const v = rec.documents[d];
      const status = (v && typeof v === "object") ? (v.status || "") : (v || "");
      const barcode = (v && typeof v === "object") ? (v.barcode || "") : "";
      const opts = statuses
        .map(o => `<option${o === status ? " selected" : ""}>${esc(o)}</option>`).join("");
      const bc = bcDocs.includes(d)
        ? `<input type="text" data-edit-barcode="${esc(d)}" value="${esc(barcode)}" placeholder="Bar code no.">`
        : `<span style="color:#9aa1ad">—</span>`;
      return `<tr><td>${n}</td><td>${esc(d)}</td>
        <td><select data-edit-doc="${esc(d)}">
              <option value=""${status ? "" : " selected"}>—</option>${opts}
            </select></td><td>${bc}</td></tr>`;
    };

    html += `<h4>Required Documents
      <span style="font-family:system-ui;font-weight:400;font-size:.75rem;color:#6a7280">
        — enter bar code numbers as documents are received, then Save</span></h4>`;

    let n = 0;
    html += `<div style="font-weight:600;color:#8c2020;margin:4px 0 6px">Mandatory documents</div>
      <table><thead><tr>
        <th style="width:34px">#</th><th>Document</th>
        <th style="width:130px">Submitted</th><th style="width:160px">Bar code no.</th>
      </tr></thead><tbody>`;
    mand.forEach(d => { n++; html += editRow(d, n, mSt); });
    html += `</tbody></table>`;

    html += `<div style="font-weight:600;color:#12315c;margin:14px 0 6px">Optional documents</div>
      <table><thead><tr>
        <th style="width:34px">#</th><th>Document</th>
        <th style="width:130px">Submitted</th><th style="width:160px">Bar code no.</th>
      </tr></thead><tbody>`;
    opt.forEach(d => { n++; html += editRow(d, n, oSt); });
    html += `</tbody></table>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn-primary" onclick="saveDocuments(${id})">Save bar codes</button>
        <span id="docSaveMsg" style="font-size:.8rem;color:#6a7280"></span>
      </div>`;
  } else {
    html += `<table>` + Object.entries(rec.data)
      .map(([k, v]) => `<tr><td class="lab">${esc(k)}</td><td>${esc(v)}</td></tr>`).join("") + `</table>`;
  }
  document.getElementById("dBody").innerHTML = html;
  document.getElementById("detail").showModal();
}

/** Persist the document status + bar code edits made in the detail dialog. */
async function saveDocuments(id) {
  const documents = {};
  document.querySelectorAll("[data-edit-doc]").forEach(sel => {
    const name = sel.dataset.editDoc;
    const bcEl = document.querySelector(`[data-edit-barcode="${CSS.escape(name)}"]`);
    const status = sel.value;
    const barcode = bcEl ? bcEl.value.trim() : "";
    if (status || barcode) documents[name] = { status, barcode };
  });

  const msg = document.getElementById("docSaveMsg");
  msg.textContent = "Saving…";
  try {
    const res = await fetch(api(`/api/admin/submissions/${id}/documents`), {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify({ documents })
    });
    if (handleAuthFailure(res)) return;
    if (!res.ok) throw new Error("save failed");
    msg.textContent = "Saved.";
    toast("Bar codes saved.");
  } catch (e) {
    msg.textContent = "Could not save.";
    toast("Could not save bar codes.", true);
  }
}

/* ---------------- edit ---------------- */
let EDIT_ID = null;

/** Open the edit form for one application, pre-filled with its saved data. */
async function openEdit(id) {
  if (!SCHEMA) await loadSchema();
  const res = await fetch(api(`/api/admin/submissions/${id}`), { headers: headers() });
  if (handleAuthFailure(res)) return;
  if (!res.ok) { toast("Could not open that application for editing.", true); return; }
  const rec = await res.json();
  EDIT_ID = id;

  document.getElementById("eTitle").textContent = `Edit — ${rec.full_name} (${rec.reference})`;

  let html = "";
  if (SCHEMA) {
    SCHEMA.sections.forEach(sec => {
      html += `<h4>${esc(sec.title)}</h4><div class="grid">`;
      sec.fields.forEach(f => { html += fieldHtml(f); });
      html += `</div>`;
    });
  }
  document.getElementById("eBody").innerHTML = html;

  // Fill in the saved values now that the inputs exist in the DOM.
  if (SCHEMA) {
    SCHEMA.sections.forEach(sec => sec.fields.forEach(f => {
      const el = document.getElementById(f.k);
      if (el) el.value = rec.data[f.k] || "";
    }));
  }

  document.getElementById("editDialog").showModal();
}

/** Save the edited fields back to the server (PATCH). */
async function saveEdit() {
  if (!EDIT_ID) return;
  const btn = document.getElementById("eSaveBtn");
  const data = {};
  document.querySelectorAll("#eBody [data-key]").forEach(el => { data[el.dataset.key] = el.value.trim(); });

  if (!data.full_name) { toast('Fill in "Full name of candidate" before saving.', true); return; }
  if (!data.cet_mobile) { toast('Fill in "CET registration mobile number" before saving.', true); return; }

  btn.disabled = true; btn.textContent = "Saving…";
  try {
    const res = await fetch(api(`/api/admin/submissions/${EDIT_ID}`), {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify({ data })
    });
    if (handleAuthFailure(res)) return;
    const out = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(out.detail || "Save failed");
    toast("Application updated.");
    document.getElementById("editDialog").close();
    loadList(PAGE);
  } catch (e) {
    toast(e.message || "Could not save changes.", true);
  } finally {
    btn.disabled = false; btn.textContent = "Save changes";
  }
}

async function removeOne(id, name) {
  if (!confirm(`Delete the application from ${name}? This cannot be undone.`)) return;
  const res = await fetch(api(`/api/admin/submissions/${id}`), { method: "DELETE", headers: headers() });
  if (handleAuthFailure(res)) return;
  if (res.ok) { toast(`Deleted — ${name}`); loadList(PAGE); }
  else toast("Could not delete that application.", true);
}

/* ---------------- downloads ----------------
   fetch + blob is used (not a plain link) so the
   Authorization header travels with the request. */
async function downloadBlob(url, fallbackName) {
  try {
    const res = await fetch(url, { headers: { "Authorization": "Bearer " + TOKEN } });
    if (handleAuthFailure(res)) return;
    if (!res.ok) {
      const out = await res.json().catch(() => ({}));
      toast(out.detail || "Download failed.", true);
      return;
    }
    const disp = res.headers.get("Content-Disposition") || "";
    const match = disp.match(/filename="?([^"]+)"?/);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = match ? match[1] : fallbackName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
    toast((a.download.endsWith(".pdf") ? "PDF" : "Excel") + " downloaded.");
  } catch (e) {
    toast("Download failed. Check your connection.", true);
  }
}

function downloadAll() {
  const q = document.getElementById("q").value.trim();
  downloadBlob(api(`/api/admin/export.xlsx?q=${encodeURIComponent(q)}`), "BFEG_Applications.xlsx");
}

function downloadOne(id) {
  downloadBlob(api(`/api/admin/submissions/${id}/export.xlsx`), "student.xlsx");
}

/** The filled application in the printed CET form layout. */
function downloadPdf(id) {
  downloadBlob(api(`/api/admin/submissions/${id}/form.pdf`), "application-form.pdf");
}

/* ---------------- boot ---------------- */
(async function () {
  if (TOKEN) {
    const res = await fetch(api("/api/admin/submissions?per_page=1"), { headers: headers() });
    if (res.ok) { showAdmin(true); await loadSchema(); loadList(1); return; }
    sessionStorage.removeItem("bfeg_token"); TOKEN = "";
  }
  showAdmin(false);
})();
