"""
Learning Engine

يحفظ نتائج العملات
ويعطي احتمال مبني على التاريخ
"""

import sqlite3
import os



DB="data/history.db"



def connect():

    os.makedirs(
        "data",
        exist_ok=True
    )

    return sqlite3.connect(DB)



def create_learning_table():


    conn=connect()

    cur=conn.cursor()


    cur.execute("""

    CREATE TABLE IF NOT EXISTS learning(

    id INTEGER PRIMARY KEY,

    symbol TEXT,

    address TEXT,

    score REAL,

    result REAL,

    created DATETIME DEFAULT CURRENT_TIMESTAMP

    )

    """)


    conn.commit()

    conn.close()




def save_prediction(
        symbol,
        address,
        score,
        result=0
):


    conn=connect()

    cur=conn.cursor()


    cur.execute("""

    INSERT INTO learning

    (
    symbol,
    address,
    score,
    result
    )

    VALUES (?,?,?,?)

    """,

    (
    symbol,
    address,
    score,
    result
    ))


    conn.commit()

    conn.close()




def prediction_score(pair):


    conn=connect()

    cur=conn.cursor()


    cur.execute("""

    SELECT AVG(result)

    FROM learning

    WHERE score > 80

    """)


    result=cur.fetchone()[0]


    conn.close()



    if result is None:

        return 50



    return max(
        0,
        min(
            result,
            100
        )
    )
