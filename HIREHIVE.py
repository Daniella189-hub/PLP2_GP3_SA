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

        user = User.load_by_email(self.db, email)
        if user is None:
            print("No profile found with that email.")
            return None

        if not user.verify_password(password):
            print("Incorrect password.")
            return None

        self.current_user = user
        print(f"Welcome back, {user.full_name}!")
        return user


if __name__ == "__main__":
    portal = JobPortal()
    while True:
        print("\n=== HireHive ===")
        print("1. Create Profile")
        print("2. Load Profile (Login)")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            portal.create_profile()
        elif choice == "2":
            portal.load_profile()
        elif choice == "3":
            portal.db.close()
            break
        else:
            print("Invalid option, try again.")
