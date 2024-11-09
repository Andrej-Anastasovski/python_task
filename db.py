import sqlite3

def get_db_connection(db_name='database.db'):
    """Establish a connection to the database."""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

def init_db(database):
    """Initialize the database with the required tables."""
    with get_db_connection(database) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                request_name TEXT NOT NULL,
                file_reference TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                result REAL,
                FOREIGN KEY (request_id) REFERENCES requests (id)
            )
        ''')
        conn.commit()

def get_results(db_path):
    """Fetch all results from the database."""
    query = '''
        SELECT r.user, r.request_name, r.file_reference, res.result 
        FROM requests r
        JOIN results res ON r.id = res.request_id
    '''
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

    return [{'user': row[0], 'request_name': row[1], 'file_reference': row[2], 'result': row[3]} for row in rows]

def check_database(db_path):
    """Check if there are any records in the requests table."""
    query = "SELECT * FROM requests"
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        records = cursor.fetchall()

    return records

def drop_db(db_name='database.db'):
    """Drop the requests and results tables."""
    queries = [
        'DROP TABLE IF EXISTS requests',
        'DROP TABLE IF EXISTS results'
    ]
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        for query in queries:
            cursor.execute(query)
        conn.commit()

def clear_db(db_name='database.db'):
    """Clear all records from the requests and results tables."""
    queries = [
        'DELETE FROM requests',
        'DELETE FROM results'
    ]
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        for query in queries:
            cursor.execute(query)
        conn.commit()
