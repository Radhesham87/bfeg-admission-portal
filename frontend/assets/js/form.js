/* ==========================================================
   USER PANEL
   Renders the form from the backend schema, validates it,
   and posts it. Students never receive the data file.
   ========================================================== */

let SCHEMA = null;

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
  html += `<section class="block"><h2><span class="num">${SCHEMA.sections.length + 1}</span>Required Documents
             <span class="help">tick the status of each document</span></h2>
           <div class="docwrap"><table><thead><tr>
             <th style="width:36px">#</th><th>Document</th><th style="width:170px">Status</th>
           </tr></thead><tbody>`;
  SCHEMA.documents.forEach((d, i) => {
    html += `<tr><td>${i + 1}</td><td>${esc(d)}</td><td>
      <select data-doc="${esc(d)}"><option value="">— select —</option>` +
      SCHEMA.doc_status.map(s => `<option>${esc(s)}</option>`).join("") +
      `</select></td></tr>`;
  });
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
  document.querySelectorAll("[data-doc]").forEach(el => {
    if (el.value) documents[el.dataset.doc] = el.value;
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
      body: JSON.stringify({ data, documents })
    });
    const out = await res.json();
    if (!res.ok) throw new Error(out.detail || "Submission failed");
    showSuccess(out.reference, data.full_name);
  } catch (err) {
    toast(err.message || "Could not submit. Try again.", true);
    btn.disabled = false;
    btn.textContent = "Submit application";
  }
}

function showSuccess(reference, name) {
  document.getElementById("page").innerHTML = `
    <div class="ok-box">
      <h2>Application received</h2>
      <p style="color:#6a7280">Thank you, ${esc(name)}. A BFEG counsellor will contact you.</p>
      <div class="ref">${esc(reference)}</div>
      <p style="font-size:.85rem;color:#6a7280">
        Save this reference number. Quote it whenever you contact BFEG about your admission.<br>
        Keep your original documents ready for verification.
      </p>
      <button class="btn-ghost" onclick="location.reload()">Submit another application</button>
    </div>`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

loadSchema();
