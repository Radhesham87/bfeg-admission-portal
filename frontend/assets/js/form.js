/* ==========================================================
   USER PANEL
   Renders the form from the backend schema, validates it,
   and posts it. Students never receive the data file.
   ========================================================== */

let SCHEMA = null;

/* ---- Pravesh Setu app launch -------------------------------------------
   The Pravesh Setu app opens this page as  …/#ps_launch=<single-use token>.
   The token is kept only for this tab, removed from the address bar, and sent
   with the submission; the server forwards it (hashed) to Pravesh Setu. */
const PS_RETURN_URL = "mobile://neet-form-return";
const PS_LAUNCH = (() => {
  try {
    const m = /(?:^#|&)ps_launch=([A-Za-z0-9_-]{43})(?:&|$)/.exec(window.location.hash || "");
    if (m) {
      sessionStorage.setItem("ps_launch", m[1]);
      history.replaceState(null, "", window.location.pathname + window.location.search);
    }
    return sessionStorage.getItem("ps_launch") || "";
  } catch (e) { return ""; }
})();

function psBanner() {
  if (!PS_LAUNCH) return;
  const note = document.createElement("div");
  note.className = "note ps-note";
  note.textContent = "Opened from the Pravesh Setu app. After you submit, a PDF of your form " +
    "will appear in Pravesh Setu → Documents → My Documents.";
  const page = document.getElementById("page");
  page.insertBefore(note, page.firstChild);
}

async function loadSchema() {
  try {
    const res = await fetch(api("/api/schema"));
    if (!res.ok) throw new Error("bad status " + res.status);
    SCHEMA = await res.json();
    renderForm();
  } catch (err) {
    document.getElementById("formArea").innerHTML =
      `<div class="card"><h3 style="margin-top:0;color:#8c2020">Cannot reach the server</h3>
       <p style="color:#6a7280;font-size:.88rem">
       The form could not load. Check that the API address in
       <code>assets/js/config.js</code> is correct and that the backend is running.<br>
       Currently pointing at: <code>${esc(window.API_BASE)}</code></p></div>`;
  }
}

function renderForm() {
  let html = "";

  SCHEMA.sections.forEach((sec, i) => {
    html += `<section class="block"><h2><span class="num">${i + 1}</span>${esc(sec.title)}` +
            (sec.help ? `<span class="help">${esc(sec.help)}</span>` : "") + `</h2><div class="grid">`;
    sec.fields.forEach(f => { html += fieldHtml(f); });
    html += `</div></section>`;
  });

  // documents checklist
  const withBarcode = SCHEMA.barcode_documents || [];
  const mandatory = SCHEMA.mandatory_documents || [];
  const optional = SCHEMA.optional_documents || [];
  const mStatus = SCHEMA.mandatory_status || ["Yes"];
  const oStatus = SCHEMA.optional_status || ["Yes", "No"];

  const docRow = (d, n, statuses) => {
    const bcCell = withBarcode.includes(d)
      ? `<input type="text" data-barcode="${esc(d)}" placeholder="Bar code no.">`
      : `<span style="color:#9aa1ad">—</span>`;
    const opts = statuses.map(o => `<option>${esc(o)}</option>`).join("");
    return `<tr><td>${n}</td><td>${esc(d)}</td><td>
      <select data-doc="${esc(d)}"><option value="">— select —</option>${opts}</select>
      </td><td>${bcCell}</td></tr>`;
  };

  html += `<section class="block"><h2><span class="num">${SCHEMA.sections.length + 1}</span>Required Documents
             <span class="help">mandatory documents must be submitted; optional documents only if applicable</span></h2>
           <div class="docwrap">`;

  // --- Mandatory group (Yes only) ---
  html += `<div style="font-family:Georgia,serif;font-weight:600;color:#8c2020;margin:2px 0 8px">
             Mandatory documents <span style="font-weight:400;font-size:.8rem;color:#6a7280">— all required</span>
           </div>
           <table><thead><tr>
             <th style="width:36px">SR.<br>NO.</th><th>DOCUMENT NAME</th>
             <th style="width:170px">SUBMIT FOR (BFEG)</th>
             <th style="width:180px">BAR CODE NO.</th>
           </tr></thead><tbody>`;
  let n = 0;
  mandatory.forEach(d => { n++; html += docRow(d, n, mStatus); });
  html += `</tbody></table>`;

  // --- Optional group (Yes / No) ---
  html += `<div style="font-family:Georgia,serif;font-weight:600;color:#12315c;margin:18px 0 8px">
             Optional documents <span style="font-weight:400;font-size:.8rem;color:#6a7280">— if applicable</span>
           </div>
           <table><thead><tr>
             <th style="width:36px">SR.<br>NO.</th><th>DOCUMENT NAME</th>
             <th style="width:170px">SUBMIT FOR (BFEG)</th>
             <th style="width:180px">BAR CODE NO.</th>
           </tr></thead><tbody>`;
  optional.forEach(d => { n++; html += docRow(d, n, oStatus); });
  html += `</tbody></table></div></section>`;

  document.getElementById("formArea").innerHTML = html;
  document.getElementById("submitCard").style.display = "";
  wireAutoPercent();
}

/* 10th and 12th percentages fill themselves in */
function wireAutoPercent() {
  ["ssc", "hsc"].forEach(p => {
    const obt = document.getElementById(p + "_obtained");
    const out = document.getElementById(p + "_out_of");
    const pct = document.getElementById(p + "_percent");
    if (!obt || !out || !pct) return;
    const calc = () => {
      const a = parseFloat(obt.value), b = parseFloat(out.value);
      if (a > 0 && b > 0) pct.value = ((a / b) * 100).toFixed(2);
    };
    obt.addEventListener("input", calc);
    out.addEventListener("input", calc);
  });
}

function collect() {
  const data = {}, documents = {};
  document.querySelectorAll("[data-key]").forEach(el => { data[el.dataset.key] = el.value.trim(); });

  // Each document carries a status and an optional bar code number.
  document.querySelectorAll("[data-doc]").forEach(el => {
    const name = el.dataset.doc;
    const bc = document.querySelector(`[data-barcode="${CSS.escape(name)}"]`);
    const status = el.value;
    const barcode = bc ? bc.value.trim() : "";
    if (status || barcode) documents[name] = { status, barcode };
  });
  return { data, documents };
}

function validate(data) {
  let firstBad = null;
  document.querySelectorAll(".f").forEach(el => el.classList.remove("bad"));

  SCHEMA.sections.forEach(sec => sec.fields.forEach(f => {
    if (!f.req) return;
    if (!data[f.k]) {
      const box = document.getElementById(f.k)?.closest(".f");
      if (box) box.classList.add("bad");
      if (!firstBad) firstBad = f;
    }
  }));
  return firstBad;
}

async function submitForm() {
  const btn = document.getElementById("submitBtn");
  const { data, documents } = collect();

  const bad = validate(data);
  if (bad) {
    toast(`Fill in "${bad.l}" before submitting.`, true);
    document.getElementById(bad.k)?.scrollIntoView({ behavior: "smooth", block: "center" });
    document.getElementById(bad.k)?.focus();
    return;
  }
  if (!document.getElementById("declare").checked) {
    toast("Tick the declaration before submitting.", true);
    return;
  }

  btn.disabled = true;
  btn.textContent = "Submitting…";
  try {
    const res = await fetch(api("/api/submissions"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(PS_LAUNCH ? { data, documents, launch_token: PS_LAUNCH } : { data, documents })
    });
    const out = await res.json();
    if (!res.ok) throw new Error(out.detail || "Submission failed");
    showSuccess(out.reference, data.full_name, out.pravesh_setu);
  } catch (err) {
    toast(err.message || "Could not submit. Try again.", true);
    btn.disabled = false;
    btn.textContent = "Submit application";
  }
}

function showSuccess(reference, name, ps) {
  // A launch token is single-use: forget it once the application is saved.
  try { sessionStorage.removeItem("ps_launch"); } catch (e) { /* ignore */ }
  let appBlock = "";
  if (PS_LAUNCH) {
    const linked = ps && ps.linked;
    appBlock = `
      <p style="font-size:.9rem;color:${linked ? "#1f6f3f" : "#8a5a00"}">
        ${linked
          ? "Linked to your Pravesh Setu account. Your form PDF is in Documents → My Documents."
          : "Saved. Pravesh Setu will finish linking your form shortly — open the app and check NEET Form status."}
      </p>
      <a class="btn-primary" style="display:inline-block;text-decoration:none;margin-bottom:10px"
         href="${PS_RETURN_URL}?ref=${encodeURIComponent(reference)}">Return to Pravesh Setu</a><br>`;
  }
  document.getElementById("page").innerHTML = `
    <div class="ok-box">
      <h2>Application received</h2>
      <p style="color:#6a7280">Thank you, ${esc(name)}. A BFEG counsellor will contact you.</p>
      <div class="ref">${esc(reference)}</div>
      <p style="font-size:.85rem;color:#6a7280">
        Save this reference number. Quote it whenever you contact BFEG about your admission.<br>
        Keep your original documents ready for verification.
      </p>
      ${appBlock}
      ${PS_LAUNCH ? "" : `<button class="btn-ghost" onclick="location.reload()">Submit another application</button>`}
    </div>`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

psBanner();
loadSchema();
