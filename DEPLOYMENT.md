# Deploying — GitHub → Netlify + Cloud Run

Two panels, two hosts:

| Part | Folder | Host |
|---|---|---|
| Student form + Admin panel | `frontend/` | **Netlify** |
| API, database, Excel & PDF export | `backend/` | **Google Cloud Run** |

Netlify serves static files only — it cannot run FastAPI. That's why the
backend goes to Cloud Run, exactly like your engineering site.

Do the parts in order: **A → B → C → D**. The frontend needs the backend's
address, so the backend must exist first.

---

# PART A — Push to GitHub

### A1. Install Git (skip if you have it)

```bash
git --version
```

No output? Install from [git-scm.com/downloads](https://git-scm.com/downloads).

### A2. Create an empty repo on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `bfeg-admission-portal`
3. Set it to **Private** — this repo relates to a system holding student
   personal data. Do not make it public.
4. **Do not** tick "Add a README" or "Add .gitignore" — the folder already
   has both, and an extra file causes a merge conflict on the first push.
5. Click **Create repository**

### A3. Open a terminal in the project folder

The folder holding `netlify.toml` and `run_local.py`.

```bash
cd path/to/bfeg-portal-repo
```

### A4. Check nothing private is about to be committed

```bash
git init
git add .
git status --short
```

Read the list. You should see `.md`, `.html`, `.js`, `.css`, `.py`,
`netlify.toml`, and the files under `backend/app/assets/`.

You must **not** see any `.db` file or a `.env`. Those hold student data and
secrets, and `.gitignore` already excludes them — if one appears, stop and
tell me before continuing.

### A5. Make the first commit

```bash
git commit -m "BFEG admission portal: student form, admin panel, Excel and PDF export"
```

If Git asks who you are, set it once:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### A6. Connect and push

Replace `YOUR-USERNAME`:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/bfeg-admission-portal.git
git push -u origin main
```

GitHub will ask to sign in. If it asks for a password, use a **personal
access token** instead ([github.com/settings/tokens](https://github.com/settings/tokens)
→ Generate new token (classic) → tick `repo`).

Refresh the repo page — your files are there.

---

# PART B — Database (Neon)

Cloud Run erases its own disk on every restart, so the database must live
elsewhere. This is the exact issue that wiped the users on your engineering
site.

### B1. Create the project

1. [neon.tech](https://neon.tech) → **New Project**
2. Name: `bfeg-portal` — a **separate** project from the engineering one,
   so the two apps' tables never mix
3. Region: Singapore if offered (closest to Mumbai Cloud Run)

### B2. Copy the connection string

Dashboard → **Connection string** → reveal the password → copy.

It must look like this, with a real password and `?sslmode=require` at the end:

```
postgresql://neondb_owner:npg_AbC123@ep-cool-name-12345.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

Paste it into Notepad. You need it in step C3.

---

# PART C — Backend to Cloud Run

### C1. Sign in to gcloud

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

(`gcloud projects list` shows your project IDs.)

### C2. Enable the services

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### C3. Generate a session secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the 64-character output.

### C4. Deploy

Open `deploy-backend.sh`, fill in the four `CHANGE-ME` values
(admin password, the JWT secret from C3, the Neon URL from B2, and
`ALLOWED_ORIGINS` — put `*` for now, you'll tighten it in D5), then:

```bash
bash deploy-backend.sh
```

Prefer typing it out? The equivalent single command:

```bash
cd backend
gcloud run deploy bfeg-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars "ADMIN_USERNAME=admin" \
  --set-env-vars "ADMIN_PASSWORD=your-long-password" \
  --set-env-vars "JWT_SECRET=paste-from-C3" \
  --set-env-vars "DATABASE_URL=paste-from-B2" \
  --set-env-vars "ALLOWED_ORIGINS=*"
```

Answer **y** to "Allow unauthenticated invocations?". That only opens the
student form — the admin routes still require the login token.

The build takes 3–5 minutes. Copy the **Service URL** it prints:

```
Service URL: https://bfeg-api-abc123xyz-el.a.run.app
```

### C5. Verify

```bash
curl https://bfeg-api-abc123xyz-el.a.run.app/api/health
```

Expect `{"status":"ok", ...}`.

Now confirm the data routes are locked:

```bash
curl -o /dev/null -w "%{http_code}\n" https://bfeg-api-abc123xyz-el.a.run.app/api/admin/export.xlsx
```

Expect **401**. If you get 200, stop — the student data is exposed.

---

# PART D — Frontend to Netlify

### D1. Connect the repo

1. [app.netlify.com](https://app.netlify.com) → **Add new site** →
   **Import an existing project**
2. Choose **GitHub**, authorise, pick `bfeg-admission-portal`

### D2. Confirm the build settings

Netlify reads `netlify.toml` and should show:

| Field | Value |
|---|---|
| Base directory | `frontend` |
| Build command | `bash set-api-url.sh` |
| Publish directory | `frontend` |

Leave them as they are.

### D3. Add the API address

Before the first deploy, click **Add environment variables**:

| Key | Value |
|---|---|
| `API_BASE` | `https://bfeg-api-abc123xyz-el.a.run.app` |

Your Cloud Run URL from C4, with **no trailing slash**.

The build script writes this into `config.js` at deploy time, so the URL
never sits in your git history and you can change backends without editing
code.

### D4. Deploy

Click **Deploy site**. About a minute. You get a URL like
`https://cheerful-panda-1a2b3c.netlify.app`.

Rename it under **Site configuration → Change site name** — e.g.
`bfeg-admission`.

### D5. Lock CORS to your site

Back in the terminal, replace `*` with the real Netlify address:

```bash
gcloud run services update bfeg-api --region asia-south1 \
  --set-env-vars "ALLOWED_ORIGINS=https://bfeg-admission.netlify.app"
```

Do not skip this. With `*`, any website can call your API and hammer the
admin login.

---

# PART E — Test the live system

1. Open `https://bfeg-admission.netlify.app` — the form should load.
   "Cannot reach the server" means `API_BASE` is wrong or CORS is not set.
2. Fill the required fields, tick the declaration, submit → you get a
   reference number.
3. Open `https://bfeg-admission.netlify.app/admin` → sign in.
4. Your application is in the list.
5. Click **PDF** → the filled 8-page form downloads.
6. Click **Download Excel** → the spreadsheet downloads.
7. **The important one:** in a private window open
   `https://bfeg-api-xxxx.a.run.app/api/admin/export.xlsx`.
   It must say *"Sign in to continue."*
8. Redeploy the backend (`bash deploy-backend.sh`) and reload the admin
   panel. Your test record must still be there — if it vanished,
   `DATABASE_URL` never reached the container.
9. Delete the test record.

---

# Making changes later

Both hosts redeploy automatically when you push.

```bash
git add .
git commit -m "describe what changed"
git push
```

- Changed anything in `frontend/` → Netlify rebuilds in about a minute
- Changed anything in `backend/` → run `bash deploy-backend.sh` again
  (Cloud Run does not watch GitHub unless you set up Cloud Build triggers)

To add or rename a form field, edit **`backend/app/fields.py` only** — the
student form, the admin detail view, the Excel columns and the PDF all read
from it. Then redeploy the backend.

---

# Your two links

| Who | Link |
|---|---|
| Students | `https://bfeg-admission.netlify.app` |
| BFEG staff | `https://bfeg-admission.netlify.app/admin` |

---

# When something breaks

| Symptom | Cause | Fix |
|---|---|---|
| Form says "Cannot reach the server" | `API_BASE` wrong or missing | Netlify → Environment variables → fix `API_BASE` → **Deploys → Trigger deploy** |
| Browser console shows a CORS error | Origin mismatch | Redo D5 with the exact Netlify URL, no trailing slash |
| Netlify build fails: "config.js not found" | Base directory wrong | Set base directory to `frontend` |
| Login says wrong password | Mismatch with deploy | Redeploy with the correct `ADMIN_PASSWORD` |
| Records vanish after redeploy | `DATABASE_URL` not set | `gcloud run services describe bfeg-api --region asia-south1` and check the env vars |
| `git push` rejected (non-fast-forward) | Remote has commits you don't | `git pull --rebase origin main` then push again |
| PDF downloads but pages 6–8 missing | Assets not copied | Confirm `backend/app/assets/` is in the repo |

---

# A note on the data you're storing

This system holds Aadhaar numbers, caste and religion, family income and
contact details — for candidates who are often minors.

- Keep the GitHub repo **private**
- Use a long `ADMIN_PASSWORD`; it is the only thing between the internet and
  every student's file
- Share the admin login only with staff who need it
- Set `ALLOWED_ORIGINS` properly (step D5)
- Delete records once a student's counselling is finished — the admin panel
  has a delete button per row
- The CET portal password is deliberately **not** collected. Anyone with
  database access could otherwise sign into a student's official CET account
  and change their choices. `COLLECT_CET_PASSWORD=true` enables it if your
  office decides otherwise — treat that as a conscious decision.
