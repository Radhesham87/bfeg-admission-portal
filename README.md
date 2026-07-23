# BFEG Admission Portal

**New here?** Two guides:

- **[LOCAL_PREVIEW.md](LOCAL_PREVIEW.md)** — run the whole site on your own
  computer in one command, no accounts needed. Start here.
- **[DEPLOYMENT.md](DEPLOYMENT.md)** — push to GitHub, deploy the panels to
  Netlify and the API to Cloud Run, step by step.

---

Two panels, one system.

| Panel | Who uses it | What it does |
|---|---|---|
| **User panel** (`index.html`) | Students | Fills the NEET-UG Maharashtra 85% application. Gets a reference number back — nothing else. |
| **Admin panel** (`admin.html`) | BFEG staff | Signs in, searches applications, views any student's full record, downloads the `.xlsx`, and downloads each application as a filled PDF in the government CET form layout. |

**Only the admin can download data.** Every list, detail and export route requires a
signed session token. Without it the API answers `401`.

```
Student browser ──► Netlify (static panels) ──► Cloud Run (FastAPI) ──► Postgres
                                                       │
                                          admin token required for
                                          /api/admin/*  and  export.xlsx
```

---

## Project layout

```
bfeg-portal/
├── backend/                 → deploys to Cloud Run
│   ├── app/
│   │   ├── fields.py        the form schema — single source of truth
│   │   ├── models.py        submissions table
│   │   ├── database.py      SQLite locally, Postgres in production
│   │   ├── security.py      admin login + JWT
│   │   ├── excel.py         builds the .xlsx workbook
│   │   ├── pdf_form.py      builds the filled CET form PDF
│   │   └── main.py          API routes
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
└── frontend/                → deploys to Netlify
    ├── index.html           user panel
    ├── admin.html           admin panel
    ├── assets/js/config.js  ← set your Cloud Run URL here
    ├── netlify.toml
    └── _redirects
```

The form has **99 fields across 8 sections plus a 14-document checklist**.
To add or rename a field, edit `backend/app/fields.py` only — the user form,
the admin detail view and the Excel columns all rebuild from it.

---

## Run it locally first

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=some-long-password
export JWT_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))")

uvicorn app.main:app --reload --port 8080
```

**Frontend**

```bash
cd frontend
python -m http.server 5173
```

Open <http://localhost:5173> for the student form and
<http://localhost:5173/admin.html> for the admin panel.
`assets/js/config.js` already points at `localhost:8080`.

---

## Deploy the backend to Cloud Run

### 1. Create a database first

Cloud Run wipes its own filesystem on every restart, so a SQLite file there
would lose all applications. Use managed Postgres — [Neon](https://neon.tech)
and [Supabase](https://supabase.com) both have a free tier, or use Cloud SQL.
Copy the connection string; it looks like:

```
postgresql://user:password@host/dbname?sslmode=require
```

### 2. Build and deploy

```bash
cd backend
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud run deploy bfeg-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars "ADMIN_USERNAME=admin" \
  --set-env-vars "ADMIN_PASSWORD=your-long-password" \
  --set-env-vars "JWT_SECRET=your-64-char-random-string" \
  --set-env-vars "DATABASE_URL=postgresql://..." \
  --set-env-vars "ALLOWED_ORIGINS=https://your-site.netlify.app"
```

`--allow-unauthenticated` lets *students* reach the form. It does **not** open
the admin routes: those are still behind the login token.

Cloud Run prints a service URL. Check it:

```bash
curl https://bfeg-api-xxxx.a.run.app/api/health
```

### 3. Keep secrets out of the command line (recommended)

```bash
echo -n "your-long-password" | gcloud secrets create bfeg-admin-password --data-file=-
gcloud run services update bfeg-api --region asia-south1 \
  --set-secrets "ADMIN_PASSWORD=bfeg-admin-password:latest"
```

---

## Deploy the frontend to Netlify

1. Open `frontend/assets/js/config.js` and set your Cloud Run URL:

   ```js
   window.API_BASE = "https://bfeg-api-xxxx.a.run.app";
   ```

2. Deploy — either drag the `frontend` folder onto
   [app.netlify.com/drop](https://app.netlify.com/drop), or connect the repo
   with **base directory** `frontend` and no build command.

3. Go back and set `ALLOWED_ORIGINS` on Cloud Run to your Netlify URL:

   ```bash
   gcloud run services update bfeg-api --region asia-south1 \
     --set-env-vars "ALLOWED_ORIGINS=https://your-site.netlify.app"
   ```

   Leaving it as `*` lets any website call your API. Set it properly before
   you share the link.

Your links become:

- Students → `https://your-site.netlify.app`
- Staff → `https://your-site.netlify.app/admin`

---

## API reference

| Method | Route | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | — | uptime check |
| GET | `/api/schema` | — | form definition |
| POST | `/api/submissions` | — | student submits |
| POST | `/api/admin/login` | — | returns a token |
| GET | `/api/admin/submissions` | token | list + search + paging |
| GET | `/api/admin/submissions/{id}` | token | full record |
| PATCH | `/api/admin/submissions/{id}/notes` | token | staff notes |
| DELETE | `/api/admin/submissions/{id}` | token | remove |
| GET | `/api/admin/export.xlsx` | token | **all applications** |
| GET | `/api/admin/submissions/{id}/export.xlsx` | token | one student |
| GET | `/api/admin/submissions/{id}/form.pdf` | token | filled CET form as PDF |

Interactive docs are at `/docs` on the running service.

---

## Handling student data responsibly

This system stores Aadhaar numbers, caste and religion, family income and
contact details for minors. A few things worth doing:

- **Set a long admin password.** It is the only thing between the internet and
  every student's personal file. Change it from the default before going live.
- **Restrict who has the login.** There is one shared admin account by design;
  do not circulate it beyond staff who need it.
- **Set `ALLOWED_ORIGINS`** to your Netlify domain rather than `*`.
- **The CET portal password is not collected.** The printed form asks for it,
  but storing it means anyone with database access could sign into a student's
  official CET account and alter their choices. If your office decides to
  collect it anyway, set `COLLECT_CET_PASSWORD=true` — please treat that as a
  deliberate decision rather than a default.
- **Delete records** once counselling for a student is finished. The admin
  panel has a delete button per row.
