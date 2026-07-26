# PLP2_GP3_SA

Kelvin Ntakirutimana

1. CV Upload
When someone applies for a job, they give a path to their CV file on their computer. My code:

Checks the file actually exists
Checks it's a real document type (PDF or Word file) — rejects things like .jpg or .txt
Copies it into a folder called uploaded_cvs/ so it's saved with the project, renamed with the user's ID and a timestamp so files never overwrite each other
Returns that saved location so it can be linked to that specific application

2. Accept / Reject Logic
This is for the admin side. My code:

Only lets someone with the admin role use it — blocks everyone else
Pulls up a list of everyone who's applied, with their name, email, and the job they applied for
Lets the admin pick one application by ID and choose accept or reject
Updates that application's status (and records when the decision was made) in the database
Immediately triggers a notification — so the applicant doesn't have to be told manually

3. Notifications

Every time a decision is made, a message gets saved in the database for that specific user
When the user logs in and checks "My Notifications," they see all their messages, newest first, with unread ones marked
Right after they view them, the messages get marked as read so they don't show up as new again
(I also added a version of this for job alerts — matching a user's listed skills against newly posted jobs and notifying them if there's a match)