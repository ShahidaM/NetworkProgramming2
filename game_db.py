import sqlite3

DATABASE = 'game.db'

def init_db():
    """Initialize the SQLite database."""
    # Connect to the database
    conn = sqlite3.connect(DATABASE)
    # Use the connection as a context manager to ensure it's closed properly
    with conn:
        # Create the 'users' table with columns 'username' and 'password'
        conn.execute('''CREATE TABLE users (username TEXT PRIMARY KEY, password TEXT)''')
        # Create the 'game' table with columns 'id', 'username', 'score', and 'last_guess'
        conn.execute('''CREATE TABLE game (
                            id INTEGER PRIMARY KEY,
                            username TEXT,
                            score INTEGER,
                            last_guess INTEGER,
                            FOREIGN KEY(username) REFERENCES users(username)
                        )''')
    # Close the database connection
    conn.close()

if __name__ == '__main__':
    # Call the init_db function when the script is executed directly
    init_db()
