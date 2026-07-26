#!/usr/bin/python3

import os
import shutil
from datetime import datetime

from job_portal import Entity


class Application(Entity):

    VALID_STATUSES = ("pending", "accepted", "rejected", "withdrawn")

    def __init__(self, user_id, job_id, status="pending", cv_path=None,
                 decision_at=None, id=None, created_at=None):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.job_id = job_id
        self.status = status
        self.cv_path = cv_path
        self.decision_at = decision_at

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of {self.VALID_STATUSES}")
        self._status = value

    def __repr__(self):
        return f"Application(user_id={self.user_id}, job_id={self.job_id}, status={self.status!r})"


class Notification(Entity):

    def __init__(self, user_id, message, is_read=False, id=None, created_at=None):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.message = message
        self.is_read = bool(is_read)

    def __repr__(self):
        flag = "read" if self.is_read else "unread"
        return f"Notification(user_id={self.user_id}, {flag}, {self.message!r})"


CV_UPLOAD_DIR = "uploaded_cvs"
ALLOWED_CV_EXTENSIONS = (".pdf", ".doc", ".docx")


def upload_cv(self):
    if self.current_user is None:
        print("You need to be logged in to upload a CV.")
        return None

    path = input("Path to your CV file (.pdf, .doc, .docx), or blank to skip: ").strip()
    if not path:
        return None

    if not os.path.isfile(path):
        print("That file doesn't exist. Please check the path and try again.")
        return None

    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_CV_EXTENSIONS:
        print(f"Unsupported file type '{ext}'. Allowed types: {ALLOWED_CV_EXTENSIONS}")
        return None

    os.makedirs(CV_UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    dest_name = f"user{self.current_user.id}_{timestamp}{ext}"
    dest_path = os.path.join(CV_UPLOAD_DIR, dest_name)

    try:
        shutil.copyfile(path, dest_path)
    except OSError as exc:
        print(f"Could not save CV: {exc}")
        return None

    print(f"CV uploaded successfully -> {dest_path}")
    return dest_path


def admin_review_applications(self):
    if self.current_user is None or not self.current_user.is_admin:
        print("Only an admin can review applications.")
        return

    rows = self.applications.get_all_with_details()
    if not rows:
        print("There are no applications to review.")
        return

    print("\n--- Applications ---")
    for row in rows:
        print(f"[{row['id']}] {row['full_name']} ({row['email']}) "
              f"applied for '{row['title']}' -- status: {row['status']}")

    raw_id = input("\nEnter application id to review (or blank to cancel): ").strip()
    if not raw_id:
        return
    if not raw_id.isdigit():
        print("Application id must be a number.")
        return

    app_id = int(raw_id)
    application = self.applications.get_by_id(app_id)
    if application is None:
        print("No application found with that id.")
        return

    if application.status != "pending":
        print(f"This application is already '{application.status}'.")
        return

    decision = input("Accept or reject? (a/r): ").strip().lower()
    if decision not in ("a", "r"):
        print("Please enter 'a' to accept or 'r' to reject.")
        return

    application.status = "accepted" if decision == "a" else "rejected"
    application.decision_at = datetime.now().isoformat()
    self.applications.update_status(application)

    message = (f"Your application (job id {application.job_id}) was "
               f"{application.status}.")
    self.notifications.create(Notification(application.user_id, message))

    print(f"Application {app_id} marked as {application.status}. Applicant notified.")


def view_notifications(self):
    """Show the logged-in user's notifications, newest first."""
    if self.current_user is None:
        print("You need to be logged in to view notifications.")
        return

    items = self.notifications.get_for_user(self.current_user.id)
    if not items:
        print("You have no notifications.")
        return

    print("\n--- Notifications ---")
    for note in items:
        flag = " " if note.is_read else "*"
        print(f"[{flag}] {note.created_at} - {note.message}")
    print("(* = unread)")


def mark_notifications_read(self):
    if self.current_user is None:
        return
    self.notifications.mark_all_read(self.current_user.id)


def send_job_alerts(self):
    if self.current_user is None or not self.current_user.is_admin:
        print("Only an admin can send job alerts.")
        return

    recent_jobs = self.jobs.most_recent(limit=5)
    if not recent_jobs:
        print("No recent jobs to alert users about.")
        return

    all_users = self.db.fetchall(
        "SELECT id, skills FROM users WHERE role = %s", ("job_seeker",)
    )

    sent = 0
    for user_row in all_users:
        user_skills = [s.strip().lower() for s in (user_row["skills"] or "").split(",") if s.strip()]
        if not user_skills:
            continue
        for job in recent_jobs:
            job_text = f"{job.title} {job.category} {job.requirements}".lower()
            if any(skill in job_text for skill in user_skills):
                message = f"New job matching your skills: '{job.title}' at {job.company}."
                self.notifications.create(Notification(user_row["id"], message))
                sent += 1

    print(f"Sent {sent} job alert notification(s).")
