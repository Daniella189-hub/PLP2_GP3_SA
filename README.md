# HireHive — Job Portal App

**Team:** Daniella · Mireille · Beryl · Shawn · Kelvin · Desire De Dieu · Belin

HireHive is a Python console application for a job portal, backed by a MySQL
database. It lets job seekers create profiles, browse and apply for jobs,
track and withdraw their applications, and receive notifications — while
admins can review applications, accept/reject them, and send job alerts.

## Setup

1. Run `Schema.sql` against your MySQL server to create the `job_portal`
   database and its tables:
   ```
   mysql -u root -p < schema.sql
   ```
2. Install dependencies:
   ```
   pip install mysql-connector-python
   ```
3. Run the app:
   ```
   python3 HIREHIVE.py
   ```
4. To make yourself an admin after registering, run:
   ```sql
   UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
   ```

## Features

- Create a profile and log in as a job seeker
- Browse and filter available job listings
- Apply for jobs, with optional CV upload (.pdf, .doc, .docx)
- View and withdraw your own applications
- Receive notifications when an application is accepted or rejected, or
  when a new job matches your listed skills
- Admins can review pending applications, accept or reject them, and
  trigger job alerts to matching users
- Permanently delete your account (with email confirmation)

## Project Structure

- `HIREHIVE.py` — model classes (`User`, `Job`, `applications`,
  `Notification`), the `JobPortal` controller, and the main menu
- `Repositories.py` — all SQL queries in the app, organized as one
  repository class per table
- `Schema.sql` — MySQL table definitions (`users`, `jobs`, `applications`,
  notifications



## Team Contributions

| Person | Assigned Work |
|---|---|
| Daniella | User authentication, credentials, validation |
| Mireille | User profile creation, save/load user data |
| Beryl | Job listings and job filtering |
| Shawn | Job application handling and viewing applications |
| Kelvin | Accept/reject logic, CV upload, notification messages |
| Desire De Dieu | Withdraw/delete application and delete account permanently |
| Belin | Main menu, application controller, database integration |

## technology used
 Python3 
 MySQL
 Object Oriented Programming
 GitHub




