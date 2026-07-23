#!/usr/bin/env python3
"""
================================================================
  BFEG ADMISSION PORTAL — LOCAL PREVIEW
================================================================

  Run this file to see the whole website on your own computer.
  No database, no cloud account, no internet needed.

      python run_local.py

  Then open:
      Student form  ->  http://localhost:8080
      Admin panel   ->  http://localhost:8080/admin.html

      Admin login   ->  admin  /  admin123

  Everything is stored in backend/bfeg_local.db (a plain file).
  Delete that file to start over.

================================================================
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
PORT = 8080

# Pin the database to one absolute path. Without this, seeding (which runs from
# the project root) and the server (which runs from backend/) would quietly use
# two different SQLite files.
DB_FILE = BACKEND / "bfeg_local.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{DB_FILE}")

# Demo credentials. These are for local preview only — the real password
# is set as an environment variable when you deploy to Cloud Run.
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("JWT_SECRET", "local-preview-secret-not-for-production")
os.environ.setdefault("ALLOWED_ORIGINS", "*")

REQUIRED = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn[standard]"),
    ("sqlalchemy", "SQLAlchemy"),
    ("openpyxl", "openpyxl"),
    ("jwt", "PyJWT"),
    ("pydantic", "pydantic"),
    ("reportlab", "reportlab"),
    ("pypdf", "pypdf"),
]


def say(msg=""):
    print(msg, flush=True)


def check_python():
    if sys.version_info < (3, 9):
        say(f"ERROR: Python 3.9 or newer is needed. You have {sys.version.split()[0]}.")
        say("Download it from https://www.python.org/downloads/")
        sys.exit(1)


def install_missing():
    """Install only what is actually missing, so re-runs are instant."""
    missing = []
    for module, package in REQUIRED:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if not missing:
        say("  All Python packages already installed.")
        return

    say(f"  Installing {len(missing)} package(s): {', '.join(missing)}")
    say("  (first run only — takes a minute)")
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", *missing]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        say()
        say("  Install failed. Try running this manually:")
        say(f"    {sys.executable} -m pip install " + " ".join(missing))
        sys.exit(1)
    say("  Done.")


def seed_demo_data():
    """Put a few sample applications in, so the admin panel isn't empty."""
    sys.path.insert(0, str(BACKEND))
    from app.database import Base, SessionLocal, engine   # noqa: E402
    from app.models import Submission                     # noqa: E402

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Submission).count() > 0:
            return 0

        samples = [
            {
                "full_name": "DEMO — Rohan Deshmukh", "neet_roll": "MH2501234",
                "neet_appno": "250100112233", "neet_rank": "18452", "neet_marks": "612",
                "pcb_total": "612", "cet_mobile": "9876543210",
                "cet_email": "rohan.demo@example.com", "father_name": "Sunil",
                "mother_name": "Asha", "gender": "Male", "dob": "2007-04-11",
                "city": "Pune", "taluka": "Haveli", "district": "Pune",
                "state": "Maharashtra", "pincode": "411038",
                "category": "OBC", "quota": "State quota", "nationality": "Indian",
                "domicile_mh": "Yes", "hsc_district": "Pune", "hsc_year": "2025",
                "hsc_rollno": "P250114", "hsc_state": "Maharashtra",
                "ssc_year": "2023", "ssc_state": "Maharashtra", "ssc_district": "Pune",
                "hsc_percent": "88.50", "ssc_percent": "91.20",
            },
            {
                "full_name": "DEMO — Sneha Patil", "neet_roll": "MH2509876",
                "neet_appno": "250100445566", "neet_rank": "9120", "neet_marks": "648",
                "pcb_total": "648", "cet_mobile": "9812345678",
                "cet_email": "sneha.demo@example.com", "father_name": "Rajesh",
                "mother_name": "Vaishali", "gender": "Female", "dob": "2007-09-02",
                "city": "Nashik", "taluka": "Nashik", "district": "Nashik",
                "state": "Maharashtra", "pincode": "422001",
                "category": "Open / General", "quota": "Both", "nationality": "Indian",
                "domicile_mh": "Yes", "hsc_district": "Nashik", "hsc_year": "2025",
                "hsc_rollno": "N250288", "hsc_state": "Maharashtra",
                "ssc_year": "2023", "ssc_state": "Maharashtra", "ssc_district": "Nashik",
                "hsc_percent": "92.00", "ssc_percent": "94.60",
            },
            {
                "full_name": "DEMO — Aditya Kulkarni", "neet_roll": "MH2504567",
                "neet_appno": "250100778899", "neet_rank": "35670", "neet_marks": "571",
                "pcb_total": "571", "cet_mobile": "9765432109",
                "cet_email": "aditya.demo@example.com", "father_name": "Mahesh",
                "mother_name": "Sunita", "gender": "Male", "dob": "2006-12-19",
                "city": "Chhatrapati Sambhajinagar", "taluka": "Aurangabad",
                "district": "Chhatrapati Sambhajinagar", "state": "Maharashtra",
                "pincode": "431001", "category": "SC", "quota": "State quota",
                "nationality": "Indian", "domicile_mh": "Yes",
                "hsc_district": "Chhatrapati Sambhajinagar", "hsc_year": "2025",
                "hsc_rollno": "A250933", "hsc_state": "Maharashtra",
                "ssc_year": "2023", "ssc_state": "Maharashtra",
                "ssc_district": "Chhatrapati Sambhajinagar",
                "hsc_percent": "79.30", "ssc_percent": "85.00",
            },
            {
                "full_name": "DEMO — Fatima Shaikh", "neet_roll": "MH2507788",
                "neet_appno": "250100223344", "neet_rank": "24310", "neet_marks": "596",
                "pcb_total": "596", "cet_mobile": "9701234567",
                "cet_email": "fatima.demo@example.com", "father_name": "Imran",
                "mother_name": "Nasreen", "gender": "Female", "dob": "2007-01-25",
                "city": "Nagpur", "taluka": "Nagpur", "district": "Nagpur",
                "state": "Maharashtra", "pincode": "440010",
                "category": "OBC", "quota": "State quota", "nationality": "Indian",
                "domicile_mh": "Yes", "minority_religious": "Muslim",
                "hsc_district": "Nagpur", "hsc_year": "2025", "hsc_rollno": "N250455",
                "hsc_state": "Maharashtra", "ssc_year": "2023",
                "ssc_state": "Maharashtra", "ssc_district": "Nagpur",
                "hsc_percent": "84.80", "ssc_percent": "89.40",
            },
            {
                "full_name": "DEMO — Prasad Jadhav", "neet_roll": "MH2502211",
                "neet_appno": "250100990011", "neet_rank": "51290", "neet_marks": "540",
                "pcb_total": "540", "cet_mobile": "9890011223",
                "cet_email": "prasad.demo@example.com", "father_name": "Baban",
                "mother_name": "Mangal", "gender": "Male", "dob": "2006-07-30",
                "city": "Latur", "taluka": "Latur", "district": "Latur",
                "state": "Maharashtra", "pincode": "413512",
                "category": "NT(B)", "quota": "State quota", "nationality": "Indian",
                "domicile_mh": "Yes", "hsc_district": "Latur", "hsc_year": "2025",
                "hsc_rollno": "L250677", "hsc_state": "Maharashtra",
                "ssc_year": "2023", "ssc_state": "Maharashtra", "ssc_district": "Latur",
                "hsc_percent": "76.10", "ssc_percent": "81.80", "pwd": "No",
            },
        ]

        docs = {
            "Admit card / hall ticket of NEET-UG": "Have it",
            "NEET-UG marksheet": "Have it",
            "H.S.C. (or equivalent) marksheet": "Have it",
            "Caste certificate": "Applying for it",
            "Domicile certificate (Maharashtra only)": "Have it",
        }

        for i, data in enumerate(samples, start=1):
            db.add(Submission(
                reference=f"BFEG-DEMO-{i:03d}",
                full_name=data["full_name"],
                neet_roll=data["neet_roll"],
                cet_mobile=data["cet_mobile"],
                cet_email=data["cet_email"],
                district=data["district"],
                category=data["category"],
                quota=data["quota"],
                data=data,
                documents=docs,
            ))
        db.commit()
        return len(samples)
    finally:
        db.close()


def main():
    say()
    say("=" * 62)
    say("  BFEG ADMISSION PORTAL — LOCAL PREVIEW")
    say("=" * 62)
    say()

    check_python()
    say(f"  Python {sys.version.split()[0]} ok")

    say()
    say("  Checking packages...")
    install_missing()

    say()
    say("  Preparing sample data...")
    try:
        added = seed_demo_data()
        if added:
            say(f"  Added {added} demo applications so the admin panel isn't empty.")
            say("  (They all start with 'DEMO —'. Delete them from the admin panel.)")
        else:
            say("  Existing data found — leaving it alone.")
    except Exception as exc:
        say(f"  Could not seed demo data ({exc}). Starting empty.")

    url = f"http://localhost:{PORT}"
    say()
    say("=" * 62)
    say(f"  Student form :  {url}")
    say(f"  Admin panel  :  {url}/admin.html")
    say(f"  API docs     :  {url}/docs")
    say()
    say(f"  Admin login  :  {os.environ['ADMIN_USERNAME']}  /  {os.environ['ADMIN_PASSWORD']}")
    say("=" * 62)
    say()
    say("  Press Ctrl+C to stop the server.")
    say()

    try:
        webbrowser.open(url)
    except Exception:
        pass

    os.chdir(BACKEND)
    import uvicorn  # noqa: E402
    uvicorn.run("app.main:app", host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say()
        say("  Server stopped.")
