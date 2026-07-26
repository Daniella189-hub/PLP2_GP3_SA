#!/usr/bin/python3

import os
import re
import shutil
import hashlib
from datetime import datetime

import mysql.connector
from mysql.connector import Error as MySQLError

from Repositories import (
    UserRepository,
    JobRepository,
    ApplicationRepository,
    NotificationRepository,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; falls back to real environment variables


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "job_portal"),
}


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class Database:
    def __init__(self, config=None):
        self._config = config or DB_CONFIG
        try:
            self._conn = mysql.connector.connect(**self._config)
            self._cursor = self._conn.cursor(dictionary=True)
        except MySQLError as exc:
            raise DatabaseError(f"Could not connect to MySQL: {exc}") from exc

    def execute(self, query, params=None, commit=False):
        try:
            self._cursor.execute(query, params or ())
            if commit:
                self._conn.commit()
            return self._cursor
        except MySQLError as exc:
            self._conn.rollback()
            raise DatabaseError(f"Query failed: {exc}\nSQL: {query}") from exc

    def fetchone(self, query, params=None):
        return self.execute(query, params).fetchone()

    def fetchall(self, query, params=None):
        return self.execute(query, params).fetchall()

    def last_insert_id(self):
        return self._cursor.lastrowid

    def close(self):
        self._cursor.close()
        if self._conn.is_connected():
            self._conn.close()
            print("Database connection closed")


class Entity:
    def __init__(self, id=None, created_at=None):
        self.id = id
        self.created_at = created_at or datetime.now().isoformat()

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value):
        self._created_at = value


# -----CLASS USER-----
class User(Entity):
    VALID_ROLES = ("job_seeker", "admin")
    _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, full_name, email, password, skills="",
                 location="", role="job_seeker", id=None, created_at=None):
        super().__init__(id, created_at)
        self.full_name = full_name
        self.email = email
        self.password = password
        self.skills = skills
        self.location = location
        self.role = role

    @property
    def full_name(self):
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        if not value or not value.strip():
            raise ValueError("Full name cannot be empty.")
        self._full_name = value.strip()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not value or not self._EMAIL_RE.match(value.strip()):
            raise ValueError(f"'{value}' is not a valid email address.")
        self._email = value.strip().lower()

    @property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, value):
        if not value or len(value) < 4:
            raise ValueError("Password must be at least 4 characters.")
        self._password_hash = hashlib.sha256(value.encode()).hexdigest()

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        if value not in self.VALID_ROLES:
            raise ValueError(f"role must be one of {self.VALID_ROLES}")
        self._role = value

    @property
    def is_admin(self):
        return self._role == "admin"

    def verify_password(self, plain_password):
        return self._password_hash == hashlib.sha256(
            plain_password.encode()).hexdigest()

    def __repr__(self):
        return f"User({self.full_name!r}, {self.email!r}, role={self.role!r})"


## ------CLASS JOB------
class Job(Entity):
  
    VALID_STATUSES = ("open", "closed")

    def __init__(self, title, company, location, category="",
                 description="", requirements="", skills_required="",
                 posted_by=None, status="open", id=None, created_at=None):
        super().__init__(id, created_at)
        self.title = title
        self.company = company
        self.location = location
        self.category = category
        self.description = description
        self.requirements = requirements
        self.skills_required = skills_required
        self.posted_by = posted_by
        self.status = status

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not value or not value.strip():
            raise ValueError("Job title cannot be empty.")
        self._title = value.strip()

    @property
    def company(self):
        return self._company

    @company.setter
    def company(self, value):
        if not value or not value.strip():
            raise ValueError("Company name cannot be empty.")
        self._company = value.strip()

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if not value or not value.strip():
            raise ValueError("Location cannot be empty.")
        self._location = value.strip()

    def requirements_as_list(self):
        return [r.strip().lower() for r in (self.requirements or "").split(",")
                if r.strip()]

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = value.strip() if value else ""

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of {self.VALID_STATUSES}")
        self._status = value

    def __repr__(self):
        return f"Job({self.title!r}, {self.company!r}, {self.location!r})"


# -----CLASS JOB APPLICATION------
class JobApplication(Entity):
    VALID_STATUSES = ("pending", "accepted", "rejected", "withdrawn")

    def __init__(self, user_id, job_id, status="pending", cv_path=None,
                 id=None, created_at=None, decision_at=None):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.job_id = job_id
        self.status = status
        self.cv_path = cv_path
        self.decision_at = decision_at

    def __repr__(self):
        return (f"JobApplication(user_id={self.user_id}, "
                f"job_id={self.job_id}, status={self.status!r})")


# ------CLASS NOTIFICATION--------
class Notification(Entity):
    def __init__(self, user_id, message, is_read=False, id=None, created_at=None):
        super().__init__(id, created_at)
        self.user_id = user_id
        self.message = message
        self.is_read = bool(is_read)

    def __repr__(self):
        flag = "read" if self.is_read else "unread"
        return f"Notification(user_id={self.user_id}, {flag}, {self.message!r})"


# ----CLASS PORTAL(connection to the repositories file and the main class we are running)------
class JobPortal(Entity):
    CV_UPLOAD_DIR = "uploaded_cvs"
    ALLOWED_CV_EXTENSIONS = (".pdf", ".doc", ".docx")

    def __init__(self):
        self.db = Database()
        self.users = UserRepository(self.db, User)
        self.jobs = JobRepository(self.db, Job)
        self.applications = ApplicationRepository(self.db, JobApplication)
        self.notifications = NotificationRepository(self.db, Notification)
        self.current_user = None

    def validate_input(self, value, field_name):
        if not value.strip():
            print(f"{field_name} cannot be empty.")
            return False
        return True

    # --1st choice--
    def create_profile(self):
        print("\n--- Create Your Profile ---")
        full_name = input("Full name: ")
        email = input("Email: ")
        password = input("Password: ")
        skills = input("Skills (comma-separated): ")
        location = input("Location: ")

        try:
            existing = self.users.get_by_email(email.strip().lower())
            if existing is not None:
                print("An account with that email already exists. "
                      "Try logging in instead.")
                return

            new_user = User(
                full_name=full_name,
                email=email,
                password=password,
                skills=skills,
                location=location,
                role="job_seeker"
            )
            self.users.create(new_user)
            self.current_user = new_user
            print(f"Profile created successfully! Welcome, {new_user.full_name}.")
        except ValueError as e:
            print(f"Could not create profile: {e}")
        except DatabaseError as e:
            print(f"Database error: {e}")

# --2 load profile--
    def load_profile(self):
        print("\n--- Load Your Profile ---")
        email = input("Email: ")
        password = input("Password: ")

        try:
            user = self.users.get_by_email(email.strip().lower())
        except DatabaseError as exc:
            print(f"Database error: {exc}")
            return None

        if user is None:
            print("No profile found with that email.")
            return None

        if not user.verify_password(password):
            print("Incorrect password.")
            return None

        self.current_user = user
        print(f"Welcome back, {user.full_name}!")
        return user


        
# --3 display jobs--
    def display_jobs(self):
        print("\n===== Available Jobs =====")
        try:
            jobs = self.jobs.get_all()
        except DatabaseError as e:
            print(f"Database error: {e}")
            return

        if not jobs:
            print("No open jobs available right now.")
            return

        for job in jobs:
            print(f"\n[{job.id}] {job.title} — {job.company}")
            print(f"    Location: {job.location}")
            if job.category:
                print(f"    category: {job.category}")
            if job.description:
                print(f"    Description: {job.description}")

    # --4th filter jobs--
    def filter_jobs(self):
        print("\n--- Filter Jobs ---")
        location_filter = input("Location (leave blank to skip): ").strip().lower()
        try:
            results = self.jobs.search(location_filter)
        except DatabaseError as e:
            print(f"Database error: {e}")
            return

        if not results:
            print("No jobs match your filters.")
            return

        print(f"\n===== {len(results)} Matching Job(s) =====")
        for job in results:
            print(f"\n[{job.id}] {job.title} — {job.company}")
            print(f"    Location: {job.location}")
            
 # --5 apply for jobs--
    def apply_for_job(self):
        print("\n--- Apply for a Job ---")

        if self.current_user is None:
            print("You must be logged in to apply for a job.")
            return

        jobs = self.jobs.get_all()
        if not jobs:
            print("No jobs available to apply for.")
            return

        for job in jobs:
            print(f"ID: {job.id} | {job.title} | {job.company} | {job.location}")

        try:
            job_id = int(input("Enter the Job ID you want to apply for: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        selected_job = self.jobs.get_by_id(job_id)
        if selected_job is None:
            print("Job not found.")
            return

        already_applied = any(
            a["job_id"] == job_id
            for a in self.applications.get_for_user(self.current_user.id)
        )
        if already_applied:
            print("You already applied for this job.")
            return

        cv_path = input("Enter path to your CV file (or press Enter to skip): ").strip()
        cv_path = cv_path if cv_path else None

        new_application = JobApplication(
            user_id=self.current_user.id, job_id=job_id, cv_path=cv_path
        )

        self.applications.create(new_application)
        print(f"Application submitted for '{selected_job.title}' at {selected_job.company}!")

    # --6th choice--
    def view_my_applications(self):
        print("\n--- My Applications ---")

        if self.current_user is None:
            print("You must be logged in to view your applications.")
            return

        my_apps = self.applications.get_for_user(self.current_user.id)
        if not my_apps:
            print("You haven't applied to any jobs yet.")
            return

        for app in my_apps:
            print(f"Application ID: {app['id']} | {app['job_title']} at "
                  f"{app['job_company']} | Status: {app['status']}")
# --7 withdraw aplication--   
    def withdraw_application(self):
        print("\n---Withdraw Application---")

        if self.current_user is None:
            print("You must be logged in to withdraw an application.")
            return
 
        try:
            application_id = int(input("Enter the Application ID to withdraw: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            return
 
        cursor = self.db.execute(
            """
            UPDATE applications
            SET status = 'withdrawn', decision_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s AND status = 'pending'
            """,
            (application_id, self.current_user.id),
            commit=True,
        )
 
        if cursor.rowcount == 0:
            print(
                "[INFO] No matching pending application found under your "
                "account (it may already be decided, withdrawn, or not yours)."
            )

            return False
 
        print(f"Application {application_id} has been withdrawn.")
        return True   

# --8 view notifications-- 
    def view_notifications(self):
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

# --9th send job alerts--
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

# --10th admin review applications--
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

# --11 delete account permanently--
    def get_account(self):
        """Fetch this user's own account row, or None if it doesn't exist."""
        return self.db.fetchone(
            "SELECT id, full_name, email FROM users WHERE id = %s",
            (self.current_user.id,),
        )

    def delete_account(self):
        if self.current_user is None:
            print("You must be logged in to delete your account.")
            return False

        print(f"\nAccount found: {self.current_user.full_name} ({self.current_user.email})")


        email_confirmation = input(
            "Type your account email to confirm deletion: "
        ).strip()

        if email_confirmation.strip().lower() != account["email"].lower():
            print("Email did not match. Account deletion cancelled.")
            return

        self.db.execute(
            "DELETE FROM users WHERE id = %s",
            (self.current_user.id,),
            commit=True,
        )
        print(f"\nAccount for {account['full_name']} has been permanently deleted.")
        self.current_user = None
        return True

        print(f"\nAccount for {self.current_user.full_name} has been permanently deleted.")
        self.current_user = None

    # --CV upload helper--
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


if __name__ == "__main__":
    try:
        portal = JobPortal()
    except DatabaseError as exc:
        print(f"Could not start: {exc}")
        raise SystemExit(1)

    print("============================================")
    print("            WELCOME TO HIREHIVE                      ")
    print("   Connecting job seekers with opportunity.")
    print("============================================")
    print("*************************")
    print("you are registering as a job seeker")
    print("-------------------------------------")
    print("enter a number to start with an action")

    while True:
        print("\n=== HireHive ===")
        print("1. Create Profile")
        print("2. Load Profile (Login)")
        print("3. Display Jobs")
        print("4. Filter Jobs")
        print("5. Apply for Job")
        print("6. View My Applications")
        print("7. Withdraw Application")
        print("8. View Notifications")
        print("9. Send Job Alerts")
        print("10. Admin Review Applications")
        print("11. Delete Account")
        print("12. Logout")
        print("13. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            portal.create_profile()
        elif choice == "2":
            portal.load_profile()
        elif choice == "3":
            portal.display_jobs()
        elif choice == "4":
            portal.filter_jobs()
        elif choice == "5":
            portal.apply_for_job()
        elif choice == "6":
            portal.view_my_applications()
        elif choice == "7":
            portal.withdraw_application()
        elif choice == "8":
            portal.view_notifications()
            portal.mark_notifications_read()
        elif choice == "9":
            portal.send_job_alerts()
        elif choice == "10":
            portal.admin_review_applications()
        elif choice == "11":
            portal.delete_account()
        elif choice == "12":
            portal.current_user = None
            print("Logged out.")
        elif choice == "13":
            portal.db.close()
            break
        else:
            print("Invalid option, try again.")
