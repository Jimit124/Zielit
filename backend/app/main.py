import secrets
import uuid

from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db, engine, Base
from .models import Customer, Upload, Contact, Segment
from .ingestion import process_upload
from .segmentation import build_query, STARTER_SEGMENTS

app = FastAPI(
    title="Zielit Data Onboarding API",
    description="Intake customer contact data (SFTP or API), load it, and find the right audience.",
    version="0.1.0",
)


# ---------- auth: one API key per customer ----------
def get_current_customer(x_api_key: str = Header(...), db: Session = Depends(get_db)) -> Customer:
    customer = db.query(Customer).filter(Customer.api_key == x_api_key).first()
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return customer


# ---------- onboarding a new customer (internal/admin use) ----------
class CustomerCreate(BaseModel):
    name: str
    contact_email: str


@app.post("/admin/customers")
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    """Provision a new customer: generates their API key and SFTP username."""
    api_key = f"zlt_{secrets.token_urlsafe(24)}"
    sftp_username = payload.name.lower().replace(" ", "-")[:32] + "-" + secrets.token_hex(3)

    customer = Customer(
        name=payload.name,
        contact_email=payload.contact_email,
        api_key=api_key,
        sftp_username=sftp_username,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {
        "customer_id": str(customer.id),
        "api_key": api_key,                 # show once; store securely on the customer's side
        "sftp_username": sftp_username,      # create matching SFTP account (see sftp_watcher/README)
        "upload_folder": f"/incoming/{sftp_username}/",
    }


# ---------- file upload (API-connection path) ----------
@app.post("/uploads")
async def upload_file(
    file: UploadFile = File(...),
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    contents = await file.read()
    upload = process_upload(db, customer.id, file.filename, contents, source="api")
    return _upload_summary(upload)


@app.get("/uploads/{upload_id}")
def get_upload(upload_id: uuid.UUID, customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.customer_id == customer.id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return _upload_summary(upload)


def _upload_summary(upload: Upload):
    return {
        "id": str(upload.id),
        "filename": upload.filename,
        "source": upload.source,
        "status": upload.status,
        "rows_seen": upload.row_count,
        "rows_loaded": upload.loaded_count,
        "rows_errored": upload.error_count,
        "errors": upload.error_report,
        "uploaded_at": upload.uploaded_at,
        "completed_at": upload.completed_at,
    }


# ---------- audience / segments ----------
class SegmentCreate(BaseModel):
    name: str
    rules: dict


@app.post("/segments")
def create_segment(payload: SegmentCreate, customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    segment = Segment(customer_id=customer.id, name=payload.name, rules=payload.rules)
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return {"id": str(segment.id), "name": segment.name, "rules": segment.rules}


@app.get("/segments/starter-templates")
def starter_templates():
    """Ready-made rule-sets a new customer can use before writing their own."""
    return STARTER_SEGMENTS


@app.get("/segments/{segment_id}/contacts")
def get_segment_contacts(segment_id: uuid.UUID, limit: int = 500, customer: Customer = Depends(get_current_customer), db: Session = Depends(get_db)):
    segment = db.query(Segment).filter(Segment.id == segment_id, Segment.customer_id == customer.id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    query = build_query(db, customer.id, segment.rules)
    contacts = query.limit(limit).all()

    return {
        "segment": segment.name,
        "matched_count": query.count(),
        "returned": len(contacts),
        "contacts": [
            {
                "email": c.email,
                "first_name": c.first_name,
                "last_name": c.last_name,
                "company": c.company,
                "industry": c.industry,
                "engagement_score": c.engagement_score,
                "consent_status": c.consent_status,
            }
            for c in contacts
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
