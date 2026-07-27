## Belin — Main Menu, Application Controller & Database Integration

This is the backbone that every other teammate's feature plugs into.

### 1. Database Integration
My code:
- Connects to the MySQL database using the provided credentials
- Wraps every query in a single `execute()` method that handles commits and
  rolls back safely if something fails
- Raises a custom `DatabaseError` instead of letting raw MySQL errors crash
  the app
- Closes the connection cleanly on exit
### 2. Application Controller — `JobPortal`
My code:
- Initializes the database connection and tracks the currently logged-in
  user (`current_user`) so every feature knows who's active
- Acts as the shared class that all teammates' methods attach to
  (profile creation, job listings, applications, notifications, etc.)
  
### 3. Main Menu
My code:
- Runs the main loop (`run()`) that prints the 13-option menu and routes
  each choice to the matching method
- Handles login/logout, and exits by closing the database connection
  gracefully

