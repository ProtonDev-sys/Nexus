import sqlite3

class DatabaseHandler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connect().close()  # Ensure the database connection is valid

    def connect(self):
        """Connect to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def execute_query(self, query, parameters=()):
        """Execute a given SQL query with optional parameters."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        conn.close()

    def fetch_all(self, query, parameters=()):
        """Fetch all results from a given SQL query with optional parameters."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def fetch_one(self, query, parameters=()):
        """Fetch a single result from a given SQL query with optional parameters."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        row = cursor.fetchone()
        conn.close()
        return row
