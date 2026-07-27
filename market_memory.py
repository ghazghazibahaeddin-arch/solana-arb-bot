import sqlite3
import os
from datetime import datetime


DB = "data/market_memory.db"


def connect():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect(DB)


def create_table():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS market_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        address TEXT,

        symbol TEXT,

        liquidity REAL,

        volume REAL,

        buys INTEGER,

        sells INTEGER,

        score REAL,

        price REAL,

        result_1h REAL DEFAULT 0,

        result_24h REAL DEFAULT 0,

        created DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()



def save_token(pair):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    INSERT INTO market_history
    (
    address,
    symbol,
    liquidity,
    volume,
    buys,
    sells,
    score,
    price
    )

    VALUES (?,?,?,?,?,?,?,?)

    """,

    (

    pair.get("baseToken",{}).get("address"),

    pair.get("baseToken",{}).get("symbol"),

    pair.get("liquidity",{}).get("usd",0),

    pair.get("volume",{}).get("h24",0),

    pair.get("txns",{}).get("h24",{}).get("buys",0),

    pair.get("txns",{}).get("h24",{}).get("sells",0),

    pair.get("score",0),

    pair.get("priceUsd",0)

    ))


    conn.commit()
    conn.close()



def get_success_patterns():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM market_history
    WHERE result_24h > 50
    """)

    data = cur.fetchall()

    conn.close()

    return data
