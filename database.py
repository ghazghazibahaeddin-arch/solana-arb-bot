import sqlite3

DB_NAME = "data/history.db"

def connect():
    return sqlite3.connect(DB_NAME)

def create_tables():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tokens(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        symbol TEXT,

        address TEXT,

        price REAL,

        liquidity REAL,

        volume REAL,

        score INTEGER,

        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()
