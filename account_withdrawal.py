#!/usr/bin/python3
"""
account_withdrawal.py
----------------------
Feature   : Withdraw Application & Delete Account Permanently
Assigned  : Desire De Dieu

"""

import mysql.connector
from mysql.connector import Error as MySQLError



class DatabaseError(Exception):
    """Raised when a database operation fails."""


class Database:
    def __init__(self, config):
        try:
            self._conn = mysql.connector.connect(**config)
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

    def close(self):
        self._cursor.close()
        if self._conn.is_connected():
            self._conn.close()


# ---------------------------------------------------------------------------
# The actual feature, as a class.
# ---------------------------------------------------------------------------
class ApplicationAccountService:


    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    # -- Feature 1: view + withdraw an application -------------------------

    def view_my_applications(self):
        """Return this user's applications (list of dict rows), newest first."""
        applications = self.db.fetchall(
            """
            SELECT a.id, j.title, j.company, a.status, a.applied_at
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            WHERE a.user_id = %s
            ORDER BY a.applied_at DESC
            """,
            (self.user_id,),
        )

        if not applications:
            print("\nYou have no applications on file.\n")
        else:
            print("\nYour applications:")
            print("-" * 70)
            for row in applications:
                print(
                    f"ID: {row['id']} | {row['title']} @ {row['company']} | "
                    f"Status: {row['status']} | Applied: {row['applied_at']}"
                )
            print("-" * 70)

        return applications

    def withdraw_application(self, application_id):

        cursor = self.db.execute(
            """
            UPDATE applications
            SET status = 'withdrawn', decision_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s AND status = 'pending'
            """,
            (application_id, self.user_id),
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

    # -- Feature 2: delete account permanently ------------------------------

    def get_account(self):
        """Fetch this user's own account row, or None if it doesn't exist."""
        return self.db.fetchone(
            "SELECT id, full_name, email FROM users WHERE id = %s",
            (self.user_id,),
        )

    def delete_account(self, email_confirmation):

        account = self.get_account()
        if account is None:
            print("[ERROR] Account not found.")
            return False

        if email_confirmation.strip().lower() != account["email"].lower():
            print("Email did not match. Account deletion cancelled.")
            return False

        self.db.execute(
            "DELETE FROM users WHERE id = %s",
            (self.user_id,),
            commit=True,
        )
        print(f"\nAccount for {account['full_name']} has been permanently deleted.")
        return True



def menu():
    print("=== Withdraw Application & Delete Account (Test Menu) ===")

    db_config = {
        "host": "mysql-23b50bcb-alustudent-6939.c.aivencloud.com",
        "user": "avnadmin",
        "password": "AVNS_ywwObOm4Kx5b-QmW0AQ",
        "database": "defaultdb",
    }

    try:
        db = Database(db_config)
    except DatabaseError as e:
        print(f"[ERROR] {e}")
        return

    try:
        user_id = int(input("Enter your user ID to log in: ").strip())
    except ValueError:
        print("[ERROR] User ID must be a number.")
        db.close()
        return

    service = ApplicationAccountService(db, user_id)

    try:
        while True:
            print("\n1. View my applications")
            print("2. Withdraw an application")
            print("3. Delete my account permanently")
            print("4. Exit")
            choice = input("Choose an option: ").strip()

            if choice == "1":
                service.view_my_applications()

            elif choice == "2":
                applications = service.view_my_applications()
                if not applications:
                    continue
                try:
                    app_id = int(input("Enter the Application ID to withdraw: ").strip())
                except ValueError:
                    print("[ERROR] Application ID must be a number.")
                    continue
                confirm = input(
                    f"Withdraw application {app_id}? This cannot be undone. (yes/no): "
                ).strip().lower()
                if confirm == "yes":
                    service.withdraw_application(app_id)
                else:
                    print("Withdrawal cancelled.")

            elif choice == "3":
                account = service.get_account()
                if account is None:
                    print("[ERROR] Account not found.")
                    continue
                print(f"\nAccount found: {account['full_name']} ({account['email']})")
                first_confirm = input(
                    "This will permanently delete your account and ALL your "
                    "applications and notifications. Continue? (yes/no): "
                ).strip().lower()
                if first_confirm != "yes":
                    print("Account deletion cancelled.")
                    continue
                email_input = input("Type your email address to confirm permanent deletion: ")
                if service.delete_account(email_input):
                    break  # account gone, exit menu

            elif choice == "4":
                print("Goodbye.")
                break

            else:
                print("Invalid option, please try again.")
    finally:
        db.close()


if __name__ == "__main__":
    menu()
