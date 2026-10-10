from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from .database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(24), unique=True, index=True, nullable=False)

    # Indexed columns power the admin search; the full form lives in `data`.
    full_name = Column(String(200), index=True, default="")
    neet_roll = Column(String(60), index=True, default="")
    cet_mobile = Column(String(30), index=True, default="")
    cet_email = Column(String(160), index=True, default="")
    district = Column(String(90), index=True, default="")
    category = Column(String(60), index=True, default="")
    quota = Column(String(40), default="")

    data = Column(JSON, nullable=False, default=dict)
    documents = Column(JSON, nullable=False, default=dict)
    notes = Column(Text, default="")

    # Pravesh Setu link: SHA-256 of the single-use launch token from the app
    # (the token itself is never stored) and the outcome of the signed event.
    ps_launch_hash = Column(String(64), index=True, default="")
    ps_sync_status = Column(String(20), default="")
    ps_sync_error = Column(Text, default="")
    ps_last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc), index=True)

    def summary(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "full_name": self.full_name,
            "neet_roll": self.neet_roll,
            "cet_mobile": self.cet_mobile,
            "cet_email": self.cet_email,
            "district": self.district,
            "category": self.category,
            "quota": self.quota,
            "pravesh_setu": self.ps_sync_status or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def detail(self):
        d = self.summary()
        d["data"] = self.data or {}
        d["documents"] = self.documents or {}
        d["notes"] = self.notes or ""
        return d
