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

