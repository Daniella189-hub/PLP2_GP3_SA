from datetime import datetime

from jobs_module import Job 


class JobApplication:
    """Represents a row in the `applications` table."""

    VALID_STATUSES = ("pending", "accepted", "rejected", "withdrawn")

    def __init__(self, user_id, job_id, status="pending", cv_path=None,
                 id=None, applied_at=None, decision_at=None):
        self.id = id
        self.user_id = user_id
        self.job_id = job_id
        self.status = status
        self.cv_path = cv_path
        self.applied_at = applied_at or datetime.now().isoformat()
        self.decision_at = decision_at

    def save(self, db):
        """Inserts this application into the applications table."""
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
        """Checks if this user has already applied to this job."""
        query = "SELECT id FROM applications WHERE user_id = %s AND job_id = %s"
        row = db.fetchone(query, (user_id, job_id))
        return row is not None

    @classmethod
    def load_by_user(cls, db, user_id):
        """Returns all applications submitted by a given user."""
        query = "SELECT * FROM applications WHERE user_id = %s"
        rows = db.fetchall(query, (user_id,))
        return [cls._from_row(row) for row in rows]

    @classmethod
    def _from_row(cls, row):
        app = cls.__new__(cls)
        app.id = row["id"]
        app.user_id = row["user_id"]
        app.job_id = row["job_id"]
        app.status = row["status"]
        app.cv_path = row.get("cv_path")
        app.applied_at = row["applied_at"]
        app.decision_at = row.get("decision_at")
        return app

    def __repr__(self):
        return f"JobApplication(user_id={self.user_id}, job_id={self.job_id}, status={self.status!r})"


def apply_for_job(db, current_user):
    """Lets the logged-in user apply to a job by ID."""
    print("\n--- Apply for a Job ---")

    jobs = Job.load_all(db)
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

    selected_job = Job.load_by_id(db, job_id)
    if selected_job is None:
        print("Job not found.")
        return

    if JobApplication.already_applied(db, current_user.id, job_id):
        print("You already applied for this job.")
        return

    cv_path = input("Enter path to your CV file (or press Enter to skip): ").strip()
    cv_path = cv_path if cv_path else None

    new_application = JobApplication(user_id=current_user.id, job_id=job_id, cv_path=cv_path)
    new_application.save(db)
    print(f"Application submitted for '{selected_job.title}' at {selected_job.company}!")


def view_my_applications(db, current_user):
    """Shows all applications submitted by the logged-in user, with job details and status."""
    print("\n--- My Applications ---")

    my_apps = JobApplication.load_by_user(db, current_user.id)
    if not my_apps:
        print("You haven't applied to any jobs yet.")
        return

    for app in my_apps:
        job = Job.load_by_id(db, app.job_id)
        job_title = job.title if job else "Unknown"
        job_company = job.company if job else "Unknown"
        print(f"Application ID: {app.id} | {job_title} at {job_company} | Status: {app.status}")
