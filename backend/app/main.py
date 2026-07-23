import os
import secrets
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .excel import build_workbook
from .fields import schema_payload
from .models import Submission
from .security import create_token, require_admin, verify_admin

Base.metadata.create_all(bind=engine)

app = FastAPI(title="BFEG Admission Portal API", version="1.0.0")

# Netlify serves the panels from a different origin, so it must be allowed here.
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- schemas ----------------
class SubmissionIn(BaseModel):
    data: dict = Field(default_factory=dict)
    documents: dict = Field(default_factory=dict)


class LoginIn(BaseModel):
    username: str
    password: str


class NotesIn(BaseModel):
    notes: str = ""


# ---------------- public ----------------
@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/api/schema")
def get_schema():
    """The user panel builds its form from this."""
    return schema_payload()


@app.post("/api/submissions", status_code=status.HTTP_201_CREATED)
def create_submission(payload: SubmissionIn, db: Session = Depends(get_db)):
    data = {k: ("" if v is None else str(v)).strip() for k, v in (payload.data or {}).items()}

    if not data.get("full_name"):
        raise HTTPException(400, "Enter the candidate's full name.")
    if not data.get("cet_mobile"):
        raise HTTPException(400, "Enter a mobile number so BFEG can contact you.")

    reference = "BFEG-" + datetime.now(timezone.utc).strftime("%y%m") + "-" + secrets.token_hex(3).upper()

    sub = Submission(
        reference=reference,
        full_name=data.get("full_name", "")[:200],
        neet_roll=data.get("neet_roll", "")[:60],
        cet_mobile=data.get("cet_mobile", "")[:30],
        cet_email=data.get("cet_email", "")[:160],
        district=data.get("district", "")[:90],
        category=data.get("category", "")[:60],
        quota=data.get("quota", "")[:40],
        data=data,
        documents=payload.documents or {},
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Students get a receipt only — never the data file.
    return {"reference": sub.reference,
            "message": "Application received. Keep this reference number safe."}


# ---------------- admin ----------------
@app.post("/api/admin/login")
def login(payload: LoginIn):
    if not verify_admin(payload.username, payload.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password.")
    return {"access_token": create_token(payload.username), "token_type": "bearer"}


@app.get("/api/admin/submissions")
def list_submissions(
    q: str = Query("", description="search name, roll no, mobile, email, district"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: str = Depends(require_admin),
):
    query = db.query(Submission)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Submission.full_name.ilike(like),
            Submission.neet_roll.ilike(like),
            Submission.cet_mobile.ilike(like),
            Submission.cet_email.ilike(like),
            Submission.district.ilike(like),
            Submission.reference.ilike(like),
        ))
    total = query.count()
    rows = (query.order_by(Submission.created_at.desc())
                 .offset((page - 1) * per_page).limit(per_page).all())
    return {"total": total, "page": page, "per_page": per_page,
            "items": [r.summary() for r in rows]}


@app.get("/api/admin/submissions/{sub_id}")
def get_submission(sub_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "That application no longer exists.")
    return sub.detail()


@app.patch("/api/admin/submissions/{sub_id}/notes")
def update_notes(sub_id: int, payload: NotesIn,
                 db: Session = Depends(get_db), _: str = Depends(require_admin)):
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "That application no longer exists.")
    sub.notes = payload.notes
    db.commit()
    return {"status": "saved"}


@app.delete("/api/admin/submissions/{sub_id}")
def delete_submission(sub_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "That application no longer exists.")
    db.delete(sub)
    db.commit()
    return {"status": "deleted"}


def _xlsx_response(rows, filename):
    content = build_workbook(rows)
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/admin/export.xlsx")
def export_all(q: str = Query(""), db: Session = Depends(get_db), _: str = Depends(require_admin)):
    query = db.query(Submission)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(
            Submission.full_name.ilike(like),
            Submission.neet_roll.ilike(like),
            Submission.cet_mobile.ilike(like),
            Submission.district.ilike(like),
        ))
    rows = query.order_by(Submission.created_at.asc()).all()
    if not rows:
        raise HTTPException(404, "No applications to export yet.")
    stamp = datetime.now().strftime("%Y%m%d")
    return _xlsx_response(rows, f"BFEG_Applications_{stamp}.xlsx")


@app.get("/api/admin/submissions/{sub_id}/export.xlsx")
def export_one(sub_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "That application no longer exists.")
    safe = "".join(ch for ch in (sub.full_name or "student") if ch.isalnum() or ch in " -_").strip()
    return _xlsx_response([sub], f"{safe or 'student'}_{sub.reference}.xlsx")


@app.get("/api/admin/submissions/{sub_id}/form.pdf")
def export_form_pdf(sub_id: int, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    """The filled application in the printed CET form layout."""
    sub = db.get(Submission, sub_id)
    if not sub:
        raise HTTPException(404, "That application no longer exists.")
    from .pdf_form import build_form_pdf
    content = build_form_pdf(sub)
    safe = "".join(ch for ch in (sub.full_name or "student") if ch.isalnum() or ch in " -_").strip()
    return StreamingResponse(
        BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition":
                 f'attachment; filename="{safe or "student"}_{sub.reference}_Form.pdf"'},
    )


# ---------------------------------------------------------------------------
# Local preview: if the frontend folder sits next to the backend, serve it from
# this same process so `python run_local.py` gives you the whole site on one
# port. In production the panels live on Netlify and this block does nothing.
# ---------------------------------------------------------------------------
_FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="frontend")
