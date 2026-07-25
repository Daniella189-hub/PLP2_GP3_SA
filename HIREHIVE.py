#!/usr/bin/python3

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime

import mysql.connector
from mysql.connector import Error as MySQLError

DB_CONFIG = {
        "host" : "mysql-23b50bcb-alustudent-6939.c.aivencloud.com",
        "port" :23055,
        "user" : "avnadmin",
        "password" : "AVNS_ywwObOm4Kx5b-QmW0AQ",
        "database": "defaultdb",
}

# ------------------------------------------------------------------
# DATABASE LAYER
# ------------------------------------------------------------------
class DatabaseError(Exception):
    """Raised when a database operation fails."""
 
 
class Database:
    """Wraps mysql-connector-python so the rest of the app never touches
    the driver directly."""
 
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
            print("Database connected successfully and exited")


# -------------------------------------------------------------------------
# Models (OOP: inheritance +encapsulation via @property)
# -------------------------------------------------------------------------

class Entity: 
    """Base class - share id/cretaed_at handling for evry model."""
    def __init__(self, id=None, created_at=None):
        self.id = id
        self.created_at = created_at or datetime.now().isoformat()
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self.id = value
    @property
    def created_at(self):
        return self._created_at


class User():
class User(Entity):
     VALID_ROLES = ("job_seeker", "admin")
    _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, full_name, email, password, skills="", location="", role="job_seeker", id=None, created_at=None):
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
    def password_hash(self):
        return self._password_hash

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


class JobPortal(Entity):
    def __init__(self):
        self.db =Database()
        self.current_user = None
    def Validate_input(self, value, field_name):
        if not value.strip():
            print(f"{field_name} cannot be empty.")
            return False
        return True

user = User("Daniella", "daniella@example.com", "hashed_password")
