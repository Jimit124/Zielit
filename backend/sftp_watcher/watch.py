"""
Runs alongside the SFTP server. Every customer gets a folder:
    /data/sftp/{sftp_username}/incoming/

This script polls those folders, and for any new file it finds:
  1. looks up the customer by their sftp_username
  2. runs it through the same process_upload() the API uses
  3. moves the file to processed/ or errors/ so it isn't picked up twice

Run this as a long-lived process (systemd service, Docker container, etc.)
next to the SFTP server — see docker-compose.yml.
"""
import os
import shutil
import time

from app.database import SessionLocal
from app.models import Customer
from app.ingestion import process_upload

SFTP_ROOT = os.getenv("SFTP_ROOT", "/data/sftp")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "15"))


def scan_once():
    db = SessionLocal()
    try:
        if not os.path.isdir(SFTP_ROOT):
            return

        for sftp_username in os.listdir(SFTP_ROOT):
            incoming = os.path.join(SFTP_ROOT, sftp_username, "incoming")
            if not os.path.isdir(incoming):
                continue

            customer = db.query(Customer).filter(Customer.sftp_username == sftp_username).first()
            if not customer:
                continue  # unknown folder, skip rather than guess

            processed_dir = os.path.join(SFTP_ROOT, sftp_username, "processed")
            errors_dir = os.path.join(SFTP_ROOT, sftp_username, "errors")
            os.makedirs(processed_dir, exist_ok=True)
            os.makedirs(errors_dir, exist_ok=True)

            for filename in os.listdir(incoming):
                filepath = os.path.join(incoming, filename)
                if not os.path.isfile(filepath) or not filename.lower().endswith(".csv"):
                    continue

                with open(filepath, "rb") as f:
                    contents = f.read()

                upload = process_upload(db, customer.id, filename, contents, source="sftp")

                dest_dir = processed_dir if upload.status == "complete" else errors_dir
                shutil.move(filepath, os.path.join(dest_dir, filename))

                print(f"[{sftp_username}] {filename}: {upload.status} "
                      f"({upload.loaded_count} loaded, {upload.error_count} errors)")
    finally:
        db.close()


if __name__ == "__main__":
    print(f"Watching {SFTP_ROOT} every {POLL_SECONDS}s...")
    while True:
        scan_once()
        time.sleep(POLL_SECONDS)
