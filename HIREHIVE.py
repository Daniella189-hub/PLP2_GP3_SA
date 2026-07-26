#!/usr/bin/python3

import hashlib
import re
from datetime import datetime

import mysql.connector
from mysql.connector import Error as MySQLError

DB_CONFIG = {
        "host": "mysql-23b50bcb-alustudent-6939.c.aivencloud.com",
        "port": 23055,
        "user": "avnadmin",
        "password": "AVNS_ywwObOm4Kx5b-QmW0AQ",
        "database": "defaultdb",
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

    def save(self, db):
        query = (
            "INSERT INTO users "
            "(full_name, email, password, skills, location, role) "
            "VALUES (%s, %s, %s, %s, %s, %s)"
        )
        params = (
            self.full_name, self.email, self._password_hash,
            self.skills, self.location, self.role
        )
        db.execute(query, params, commit=True)
        self.id = db.last_insert_id()
        return self

    @classmethod
    def load_by_email(cls, db, email):
        query = "SELECT * FROM users WHERE email = %s"
        row = db.fetchone(query, (email.strip().lower(),))
        if row is None:
            return None
        return cls._from_row(row)

    @classmethod
    def load_by_id(cls, db, user_id):
        query = "SELECT * FROM users WHERE id = %s"
        row = db.fetchone(query, (user_id,))
        if row is None:
            return None
        return cls._from_row(row)

    @classmethod
    def _from_row(cls, row):
        user = cls.__new__(cls)
        Entity.__init__(user, id=row["id"], created_at=row["created_at"])
        user._full_name = row["full_name"]
        user._email = row["email"]
        user._password_hash = row["password"]
        user.skills = row.get("skills") or ""
        user.location = row.get("location") or ""
        user._role = row["role"]
        return user

    def verify_password(self, plain_password):
        return self._password_hash == hashlib.sha256(
            plain_password.encode()).hexdigest()

    def __repr__(self):
        return f"User({self.full_name!r}, {self.email!r}, role={self.role!r})"
class Job(Entity):
    VALID_STATUSES = ("open", "closed")

    def __init__(self, title, company, location, skills_required,
                 description="", posted_by=None, status="open",
                 id=None, created_at=None):
        super().__init__(id, created_at)
        self.title = title
        self.company = company
        self.location = location
        self.skills_required = skills_required
        self.description = description
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

    @property
    def skills_required(self):
        return self._skills_required

    @skills_required.setter
    def skills_required(self, value):
        self._skills_required = value.strip() if value else ""

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in self.VALID_STATUSES:
            raise ValueError(f"status must be one of {self.VALID_STATUSES}")
        self._status = value

    def skills_as_list(self):
        return [s.strip().lower() for s in self._skills_required.split(",") if s.strip()]

    def save(self, db):
        query = (
            "INSERT INTO jobs "
            "(title, company, location, skills_required, description, posted_by, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        params = (
            self.title, self.company, self.location,
            self.skills_required, self.description, self.posted_by, self.status
        )
        db.execute(query, params, commit=True)
        self.id = db.last_insert_id()
        return self

    @classmethod
    def load_by_id(cls, db, job_id):
        query = "SELECT * FROM jobs WHERE id = %s"
        row = db.fetchone(query, (job_id,))
        if row is None:
            return None
        return cls._from_row(row)

    @classmethod
    def load_all_open(cls, db):
        query = "SELECT * FROM jobs WHERE status = %s ORDER BY created_at DESC"
        rows = db.fetchall(query, ("open",))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row):
        job = cls.__new__(cls)
        Entity.__init__(job, id=row["id"], created_at=row["created_at"])
        job._title = row["title"]
        job._company = row["company"]
        job._location = row["location"]
        job._skills_required = row.get("skills_required") or ""
        job.description = row.get("description") or ""
        job.posted_by = row.get("posted_by")
        job._status = row["status"]
        return job

    def __repr__(self):
        return f"Job({self.title!r}, {self.company!r}, {self.location!r})"


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

    def save(self, db):
        query = (
            "INSERT INTO applications (user_id, job_id, status, cv_path) "
            "VALUES (%s, %s, %s, %s)"
        )
        params = (self.user_id, self.job_id, self.status, self.cv_path)
        db.execute(query, params, commit=True)
        self.id = db.last_insert_id()
        return self

    @classmethod
    def already_applied(cls, db, user_id, job_id):
        query = "SELECT id FROM applications WHERE user_id = %s AND job_id = %s"
        row = db.fetchone(query, (user_id, job_id))
        return row is not None

    @classmethod
    def load_by_user(cls, db, user_id):
        query = "SELECT * FROM applications WHERE user_id = %s"
        rows = db.fetchall(query, (user_id,))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row):
        app = cls.__new__(cls)
        Entity.__init__(app, id=row["id"], created_at=row["applied_at"])
        app.user_id = row["user_id"]
        app.job_id = row["job_id"]
        app.status = row["status"]
        app.cv_path = row.get("cv_path")
        app.decision_at = row.get("decision_at")
        return app

    def __repr__(self):
        return f"JobApplication(user_id={self.user_id}, job_id={self.job_id}, status={self.status!r})"

class JobPortal(Entity):
    def __init__(self):
        self.db = Database()
        self.current_user = None

    def validate_input(self, value, field_name):
        if not value.strip():
            print(f"{field_name} cannot be empty.")
            return False
        return True

    def create_profile(self):
        print("\n--- Create Your Profile ---")
        full_name = input("Full name: ")
        email = input("Email: ")
        password = input("Password: ")
        skills = input("Skills (comma-separated): ")
        location = input("Location: ")

        try:
            new_user = User(
                full_name=full_name,
                email=email,
                password=password,
                skills=skills,
                location=location,
                role="job_seeker"
            )
            new_user.save(self.db)
            self.current_user = new_user
            print(f"Profile created successfully! Welcome, {new_user.full_name}.")
        except ValueError as e:
            print(f"Could not create profile: {e}")
        except DatabaseError as e:
            print(f"Database error: {e}")

    def load_profile(self):
        print("\n--- Load Your Profile ---")
        email = input("Email: ")
        password = input("Password: ")
        
        try:
            user = User.load_by_email(self.db, email)
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
    def apply_for_job(self):
        print("\n--- Apply for a Job ---")

        if self.current_user is None:
            print("You must be logged in to apply for a job.")
            return

        jobs = Job.load_all(self.db)
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

        selected_job = Job.load_by_id(self.db, job_id)
        if selected_job is None:
            print("Job not found.")
            return

        if JobApplication.already_applied(self.db, self.current_user.id, job_id):
            print("You already applied for this job.")
            return

        cv_path = input("Enter path to your CV file (or press Enter to skip): ").strip()
        cv_path = cv_path if cv_path else None

        new_application = JobApplication(user_id=self.current_user.id, job_id=job_id, cv_path=cv_path)
        new_application.save(self.db)
        print(f"Application submitted for '{selected_job.title}' at {selected_job.company}!")

    def view_my_applications(self):
        print("\n--- My Applications ---")

        if self.current_user is None:
            print("You must be logged in to view your applications.")
            return

        my_apps = JobApplication.load_by_user(self.db, self.current_user.id)
        if not my_apps:
            print("You haven't applied to any jobs yet.")
            return

        for app in my_apps:
            job = Job.load_by_id(self.db, app.job_id)
            job_title = job.title if job else "Unknown"
            job_company = job.company if job else "Unknown"
            print(f"Application ID: {app.id} | {job_title} at {job_company} | Status: {app.status}")


if __name__ == "__main__":
    try:
        db = Database()
    except DatabaseError as exc:
        print(f"Could not start: {exc}")
        print("See errors.log for the full details.")
        raise SystemExit(1)
    portal = JobPortal()

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

            
    def display_jobs(self):
        print("\n===== Available Jobs =====")
        try:
            jobs = Job.load_all_open(self.db)
        except DatabaseError as e:
            print(f"Database error: {e}")
            return

        if not jobs:
            print("No open jobs available right now.")
            return

        for job in jobs:
            print(f"\n[{job.id}] {job.title} — {job.company}")
            print(f"    Location: {job.location}")
            print(f"    Skills: {job.skills_required}")
            if job.description:
                print(f"    Description: {job.description}")


    def filter_jobs(self):
        print("\n--- Filter Jobs ---")
        location_filter = input("Location (leave blank to skip): ").strip().lower()
        skill_filter = input("Skill keyword (leave blank to skip): ").strip().lower()

        try:
            jobs = Job.load_all_open(self.db)
        except DatabaseError as e:
            print(f"Database error: {e}")
            return

        results = []
        for job in jobs:
            if location_filter and location_filter not in job.location.lower():
                continue
            if skill_filter and skill_filter not in job.skills_as_list() and \
               skill_filter not in job.skills_required.lower():
                continue
            results.append(job)

        if not results:
            print("No jobs match your filters.")
            return

        print(f"\n===== {len(results)} Matching Job(s) =====")
        for job in results:
            print(f"\n[{job.id}] {job.title} — {job.company}")
            print(f"    Location: {job.location}")
            print(f"    Skills: {job.skills_required}")

    
