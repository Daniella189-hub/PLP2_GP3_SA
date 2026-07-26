#!/usr/bin/python3
import os
import shutil
from datetime import datetime

from notification_service import NotificationService

UPLOAD_DIR = "uploads/cvs"
ALLOWED_EXTENSIONS = (".pdf", ".doc", ".docx")


class ApplicationService:

    def __init__(self, db):
        self.db = db
        self.notifier = NotificationService(db)
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    def upload_cv(self, application_id, source_path):
        source_path = source_path.strip().strip('"')

        if not source_path:
            print("No file path provided.")
            return False

        if not os.path.isfile(source_path):
            print(f"File not found: {source_path}")
            return False

        ext = os.path.splitext(source_path)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")
            return False

        filename = f"app{application_id}_{os.path.basename(source_path)}"
        dest_path = os.path.join(UPLOAD_DIR, filename)

        try:
            shutil.copy(source_path, dest_path)
        except OSError as e:
            print(f"Could not copy file: {e}")
            return False

        self.db.cur.execute(
            "UPDATE applications SET cv_path = ? WHERE id = ?",
            (dest_path, application_id)
        )
        self.db.conn.commit()
        print(f"CV uploaded and linked to application #{application_id}.")
        return True

    def list_pending(self):
        self.db.cur.execute(
            """
            SELECT a.id, u.full_name, u.email, j.title, a.cv_path
            FROM applications a
            JOIN users u ON a.user_id = u.id
            JOIN jobs j ON a.job_id = j.id
            WHERE a.status = 'pending'
            """
        )
        return self.db.cur.fetchall()

    def update_status(self, application_id, new_status):
        if new_status not in ("accepted", "rejected"):
            print("Invalid status. Must be 'accepted' or 'rejected'.")
            return False

        self.db.cur.execute("SELECT user_id FROM applications WHERE id = ?", (application_id,))
        row = self.db.cur.fetchone()
        if not row:
            print(f"No application found with id {application_id}.")
            return False

        user_id = row[0]

        self.db.cur.execute(
            "UPDATE applications SET status = ?, decision_at = ? WHERE id = ?",
            (new_status, datetime.now().isoformat(), application_id)
        )
        self.db.conn.commit()

        message = (
            f"Congratulations! Your application (#{application_id}) has been accepted."
            if new_status == "accepted"
            else f"Sorry, your application (#{application_id}) was rejected."
        )
        self.notifier.send(user_id, message)

        print(f"Application #{application_id} marked as {new_status}. Applicant notified.")
        return True

    def review_menu(self):
        rows = self.list_pending()
        if not rows:
            print("No pending applications to review.")
            return

        print("\n--- Pending Applications ---")
        for row in rows:
            cv_display = row[4] if row[4] else "No CV uploaded"
            print(f"App ID: {row[0]} | {row[1]} ({row[2]}) | Job: {row[3]} | CV: {cv_display}")

        try:
            app_id = int(input("Enter application ID to review: "))
        except ValueError:
            print("Invalid ID.")
            return

        decision = input("Type ACCEPT or REJECT: ").strip().upper()
        if decision not in ("ACCEPT", "REJECT"):
            print("Invalid decision.")
            return

        self.update_status(app_id, "accepted" if decision == "ACCEPT" else "rejected")
