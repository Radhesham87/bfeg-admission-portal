# START HERE — See the website on your own computer

No database, no cloud account, no internet needed. One command.

---

## Step 1 — Install Python (skip if you have it)

Check first. Open a terminal and type:

```bash
python --version
```

If it prints `Python 3.9` or higher, you're set. If not, get it from
[python.org/downloads](https://www.python.org/downloads/).

> **Windows users:** during install, tick the box that says
> **"Add Python to PATH"**. It is easy to miss and nothing works without it.

---

## Step 2 — Open the folder in VS Code

1. Open VS Code
2. **File → Open Folder…**
3. Choose the `bfeg-local` folder (the one holding `run_local.py`)

---

## Step 3 — Run it

Pick whichever is easiest:

**In VS Code:** press **F5**

**Or in the VS Code terminal** (Terminal → New Terminal):

```bash
python run_local.py
```

**Or without VS Code:** double-click `START_WINDOWS.bat`
(Mac/Linux: `START_MAC_LINUX.sh`)

The first run installs a few Python packages and takes about a minute.
Later runs start in a couple of seconds.

---

## Step 4 — Look around

Your browser opens automatically. If it doesn't, visit these:

| What | Address |
|---|---|
| **Student form** (user panel) | http://localhost:8080 |
| **Admin panel** | http://localhost:8080/admin.html |
| API docs | http://localhost:8080/docs |

**Admin login:** `admin` / `admin123`

Five sample applications are already loaded, so the admin panel has something
to show. They all begin with **DEMO —**.

---

## Step 5 — Try the real flow

1. Open the **student form**, fill it in, submit → you get a reference number
2. Open the **admin panel**, sign in → your new application is in the list
3. Click a reference number → the full record opens
4. Click **Download filled form (PDF)** → the application in the government
   CET form layout, ready to print and file
5. Click **Download Excel** → the `.xlsx` lands in your Downloads folder
6. Delete the DEMO rows when you're done looking

**Worth testing:** open http://localhost:8080/api/admin/export.xlsx in a
private window (not signed in). It returns *"Sign in to continue."* — that's
the proof students cannot reach anyone's data.

---

## Stopping and resetting

Press **Ctrl + C** in the terminal to stop the server.

All data sits in one file: `backend/bfeg_local.db`.
Delete it and run again to start completely fresh.

---

## Changing the form

Every field comes from **one file**: `backend/app/fields.py`.

Add, rename or remove a field there and three things update by themselves:
the student form, the admin detail view, and the Excel columns. Restart the
server to see the change.

Example — adding a field to the personal section:

```python
{"k": "whatsapp_no", "l": "WhatsApp number"},
```

---

## What's in this folder

```
bfeg-local/
├── run_local.py          ← run this
├── START_WINDOWS.bat     ← or double-click this
├── START_MAC_LINUX.sh
├── LOCAL_PREVIEW.md      ← you are here
├── README.md             ← deployment guide (for later)
├── backend/              → goes to Cloud Run when you deploy
│   └── app/
│       ├── fields.py     the form definition
│       ├── main.py       API routes
│       ├── excel.py      builds the .xlsx
│       ├── pdf_form.py   builds the filled PDF form
│       ├── security.py   admin login
│       ├── models.py     database table
│       └── database.py   SQLite here, Postgres in production
└── frontend/             → goes to Netlify when you deploy
    ├── index.html        student panel
    ├── admin.html        admin panel
    └── assets/
```

---

## When you're happy with it

Read **README.md** for the Netlify + Cloud Run deployment steps.

The only file you edit before deploying is
`frontend/assets/js/config.js` — put your Cloud Run URL in `PRODUCTION_API`.
It already detects localhost automatically, so local previews keep working
after you set it.

---

## Trouble

| Problem | Fix |
|---|---|
| `python: command not found` | Python isn't installed or not on PATH. Reinstall with "Add to PATH" ticked. |
| `Port 8080 is already in use` | Something else is on that port. Stop it, or change `PORT = 8080` near the top of `run_local.py`. |
| Browser shows "Cannot reach the server" | The server isn't running. Check the terminal for errors. |
| Blank page | Hard-refresh with **Ctrl + Shift + R**. |
| Admin login fails | Username `admin`, password `admin123` — both lowercase. |
