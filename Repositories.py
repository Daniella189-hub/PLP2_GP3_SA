#!/usr/bin/python3
"""
repositories.py
----------------
Data-access layer for the HireHive job portal. Every SQL query in the
whole app lives in this file. BaseRepository defines the contract every
repository follows (get_by_id/delete); each concrete class below adds
the queries specific to its table and knows how to turn a raw MySQL
row into the matching model object from job_portal.py.
"""

from abc import ABC, abstractmethod


class BaseRepository(ABC):
    table_name = None

    def __init__(self, db, model_cls):
        self.db = db
        self.model_cls = model_cls  # the model class this repo builds, e.g. User

    @abstractmethod
    def _row_to_model(self, row):
        """Convert a dict row from MySQL into the matching model object."""

    def get_by_id(self, id_):
        row = self.db.fetchone(f"SELECT * FROM {self.table_name} WHERE id = %s", (id_,))
        return self._row_to_model(row) if row else None

    def delete(self, id_):
        self.db.execute(f"DELETE FROM {self.table_name} WHERE id = %s", (id_,), commit=True)


class UserRepository(BaseRepository):
    table_name = "users"

    def _row_to_model(self, row):
        return self.model_cls(row["full_name"], row["email"], row["password"], row["skills"],
                    row["location"], row["role"], row["id"], row["created_at"])

    def create(self, user):
        self.db.execute(
            """INSERT INTO users (full_name, email, password, skills, location, role)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user.full_name, user.email, user.password_hash, user.skills,
             user.location, user.role), commit=True,
        )
        user.id = self.db.last_insert_id()
        return user

    def get_by_email(self, email):
        row = self.db.fetchone("SELECT * FROM users WHERE email = %s", (email,))
        return self._row_to_model(row) if row else None


class JobRepository(BaseRepository):
    table_name = "jobs"

    def _row_to_model(self, row):
        return self.model_cls(row["title"], row["company"], row["location"], row["category"],
                    row["description"], row["requirements"], row["id"], row["posted_at"])

    def create(self, job):
        self.db.execute(
            """INSERT INTO jobs (title, company, location, category, description, requirements)
               SELECT %s, %s, %s, %s, %s, %s FROM DUAL
               WHERE NOT EXISTS (SELECT 1 FROM jobs WHERE title = %s AND company = %s)""",
            (job.title, job.company, job.location, job.category, job.description,
             job.requirements, job.title, job.company), commit=True,
        )
        return job

    def get_all(self):
        rows = self.db.fetchall("SELECT * FROM jobs ORDER BY posted_at DESC")
        return [self._row_to_model(r) for r in rows]

    def search(self, keyword):
        like = f"%{keyword}%"
        rows = self.db.fetchall(
            """SELECT * FROM jobs WHERE title LIKE %s OR company LIKE %s
               OR location LIKE %s OR category LIKE %s""",
            (like, like, like, like),
        )
        return [self._row_to_model(r) for r in rows]

    def most_recent(self, limit=3):
        rows = self.db.fetchall("SELECT * FROM jobs ORDER BY posted_at DESC LIMIT %s", (limit,))
        return [self._row_to_model(r) for r in rows]


class ApplicationRepository(BaseRepository):
    table_name = "applications"

    def _row_to_model(self, row):
        return self.model_cls(row["user_id"], row["job_id"], row["status"], row["cv_path"],
                            row["decision_at"], row["id"], row["applied_at"])

    def create(self, application):
        self.db.execute(
            "INSERT INTO applications (user_id, job_id, status, cv_path) VALUES (%s, %s, %s, %s)",
            (application.user_id, application.job_id, application.status,
             application.cv_path), commit=True,
        )
        application.id = self.db.last_insert_id()
        return application

    def get_for_user(self, user_id):
        return self.db.fetchall(
            """SELECT a.*, j.title AS job_title, j.company AS job_company
               FROM applications a JOIN jobs j ON a.job_id = j.id WHERE a.user_id = %s""",
            (user_id,),
        )

    def get_all_with_details(self):
        return self.db.fetchall(
            """SELECT a.id, u.full_name, u.email, j.title, a.status
               FROM applications a JOIN users u ON a.user_id = u.id
               JOIN jobs j ON a.job_id = j.id"""
        )

    def update_status(self, application):
        self.db.execute(
            "UPDATE applications SET status = %s, decision_at = %s WHERE id = %s",
            (application.status, application.decision_at, application.id), commit=True,
        )

    def delete_for_user(self, application_id, user_id):
        self.db.execute(
            "DELETE FROM applications WHERE id = %s AND user_id = %s",
            (application_id, user_id), commit=True,
        )

    def delete_all_for_user(self, user_id):
        self.db.execute("DELETE FROM applications WHERE user_id = %s", (user_id,), commit=True)


class NotificationRepository(BaseRepository):
    table_name = "notifications"

    def _row_to_model(self, row):
        return self.model_cls(row["user_id"], row["message"], bool(row["is_read"]),
                             row["id"], row["created_at"])

    def create(self, notification):
        self.db.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (notification.user_id, notification.message), commit=True,
        )
        notification.id = self.db.last_insert_id()
        return notification

    def get_for_user(self, user_id):
        rows = self.db.fetchall(
            "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (user_id,)
        )
        return [self._row_to_model(r) for r in rows]

    def mark_all_read(self, user_id):
        self.db.execute("UPDATE notifications SET is_read = 1 WHERE user_id = %s",
                         (user_id,), commit=True)

    def delete_all_for_user(self, user_id):
        self.db.execute("DELETE FROM notifications WHERE user_id = %s", (user_id,), commit=True)
