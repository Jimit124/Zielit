"""
Turns a customer's file into rows in `contacts`.

Works the same way regardless of whether the file arrived over SFTP
(picked up by sftp_watcher/watch.py) or through the API (POST /uploads).
Both paths call `process_upload()` below.
"""
import csv
import io
import re
from datetime import datetime, date

from email_validator import validate_email, EmailNotValidError
from sqlalchemy.orm import Session

from .models import Upload, Contact

REQUIRED_COLUMNS = {"email"}

OPTIONAL_COLUMNS = {
    "first_name", "last_name", "company", "industry", "job_title",
    "country", "engagement_score", "last_purchase_date",
    "consent_status", "consent_date", "tags",
}

VALID_CONSENT = {"opted_in", "opted_out", "unknown"}


def _parse_date(value: str):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_tags(value: str):
    if not value:
        return []
    return [t.strip() for t in re.split(r"[;,]", value) if t.strip()]


def process_upload(db: Session, customer_id, filename: str, file_bytes: bytes, source: str) -> Upload:
    """Validate + load one file. Bad rows are skipped and recorded, not fatal."""

    upload = Upload(customer_id=customer_id, filename=filename, source=source, status="processing")
    db.add(upload)
    db.commit()
    db.refresh(upload)

    errors = []
    loaded = 0
    row_count = 0

    try:
        text = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        header = {h.strip().lower() for h in (reader.fieldnames or [])}
        missing = REQUIRED_COLUMNS - header
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(missing)}")

        for i, raw_row in enumerate(reader, start=2):  # row 1 is the header
            row_count += 1
            row = {k.strip().lower(): (v or "").strip() for k, v in raw_row.items() if k}

            email = row.get("email", "")
            try:
                valid = validate_email(email, check_deliverability=False)
                email = valid.normalized.lower()
            except EmailNotValidError as e:
                errors.append({"row": i, "reason": f"invalid email: {e}"})
                continue

            consent = row.get("consent_status", "unknown").lower() or "unknown"
            if consent not in VALID_CONSENT:
                consent = "unknown"

            engagement_raw = row.get("engagement_score", "0")
            try:
                engagement = max(0, min(100, int(float(engagement_raw)))) if engagement_raw else 0
            except ValueError:
                engagement = 0

            existing = (
                db.query(Contact)
                .filter(Contact.customer_id == customer_id, Contact.email == email)
                .first()
            )

            fields = dict(
                first_name=row.get("first_name") or None,
                last_name=row.get("last_name") or None,
                company=row.get("company") or None,
                industry=row.get("industry") or None,
                job_title=row.get("job_title") or None,
                country=row.get("country") or None,
                engagement_score=engagement,
                last_purchase_date=_parse_date(row.get("last_purchase_date", "")),
                consent_status=consent,
                consent_date=_parse_date(row.get("consent_date", "")),
                tags=_parse_tags(row.get("tags", "")),
                source_upload_id=upload.id,
            )

            if existing:
                for k, v in fields.items():
                    if v not in (None, [], ""):
                        setattr(existing, k, v)
                existing.updated_at = datetime.utcnow()
            else:
                db.add(Contact(customer_id=customer_id, email=email, **fields))

            loaded += 1

        db.commit()
        upload.status = "complete"

    except Exception as e:
        db.rollback()
        upload.status = "failed"
        errors.append({"row": 0, "reason": str(e)})

    upload.row_count = row_count
    upload.loaded_count = loaded
    upload.error_count = len(errors)
    upload.error_report = errors[:200]  # cap stored errors
    upload.completed_at = datetime.utcnow()
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload
