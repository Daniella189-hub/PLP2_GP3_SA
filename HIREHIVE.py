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
    """Handles the connection to MySQL and runs queries for the whole app."""

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


class JobPortal:
    """
    The main controller for the app. Holds the database connection and
    the current logged-in user, and connects the menu options to the
    right methods (some of these methods are being added by teammates).
    """

    def __init__(self):
        self.db = Database()
        self.current_user = None

    def run(self):
        """Starts the main menu loop."""
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
                self.create_profile()
            elif choice == "2":
                self.load_profile()
            elif choice == "3":
                self.display_jobs()
            elif choice == "4":
                self.filter_jobs()
            elif choice == "5":
                self.apply_for_job()
            elif choice == "6":
                self.view_my_applications()
            elif choice == "7":
                self.withdraw_application()
            elif choice == "8":
                self.view_notifications()
                self.mark_notifications_read()
            elif choice == "9":
                self.send_job_alerts()
            elif choice == "10":
                self.admin_review_applications()
            elif choice == "11":
                self.delete_account()
            elif choice == "12":
                self.current_user = None
                print("Logged out.")
            elif choice == "13":
                self.db.close()
                break
            else:
                print("Invalid option, try again.")


if __name__ == "__main__":
    try:
        portal = JobPortal()
    except DatabaseError as exc:
        print(f"Could not start: {exc}")
        raise SystemExit(1)

    portal.run()