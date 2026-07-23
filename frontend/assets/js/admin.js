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
  tbody.innerHTML = `<tr><td colspan="11" class="empty">Loading…</td></tr>`;

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
      tbody.innerHTML = `<tr><td colspan="11" class="empty">No applications found.</td></tr>`;
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

  let html = "";
  if (SCHEMA) {
    SCHEMA.sections.forEach(sec => {
      html += `<h4>${esc(sec.title)}</h4><table>`;
      sec.fields.forEach(f => {
        html += `<tr><td class="lab">${esc(f.l)}</td><td>${esc(rec.data[f.k] || "—")}</td></tr>`;
      });
      html += `</table>`;
    });
    html += `<h4>Required Documents</h4><table>`;
    SCHEMA.documents.forEach(d => {
      html += `<tr><td class="lab">${esc(d)}</td><td>${esc(rec.documents[d] || "—")}</td></tr>`;
    });
    html += `</table>`;
  } else {
    html += `<table>` + Object.entries(rec.data)
      .map(([k, v]) => `<tr><td class="lab">${esc(k)}</td><td>${esc(v)}</td></tr>`).join("") + `</table>`;
  }
  document.getElementById("dBody").innerHTML = html;
  document.getElementById("detail").showModal();
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
