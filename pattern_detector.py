"""
Pattern Detector

Compares new tokens
with historical winners.
"""

import sqlite3



DB="data/history.db"



def similarity(
    current,
    old
):


    score = 0



    # Liquidity similarity

    if current["liquidity"] >= old["liquidity"] * 0.5:

        score += 25



    # Volume

    if current["volume"] >= old["volume"] * 0.5:

        score += 25



    # Holders

    if current["holders"] >= old["holders"] * 0.5:

        score += 25



    # Buy pressure

    if current["buys"] > current["sells"]:

        score += 25



    return score




def detect_pattern(pair):


    current = {

        "liquidity":
        pair.get(
            "liquidity",
            {}
        ).get(
            "usd",
            0
        ),


        "volume":
        pair.get(
            "volume",
            {}
        ).get(
            "h24",
            0
        ),


        "holders":
        pair.get(
            "holders",
            0
        ),


        "buys":
        pair.get(
            "txns",
            {}
        )
        .get(
            "h24",
            {}
        )
        .get(
            "buys",
            0
        ),


        "sells":
        pair.get(
            "txns",
            {}
        )
        .get(
            "h24",
            {}
        )
        .get(
            "sells",
            0
        )

    }



    conn = sqlite3.connect(
        DB
    )


    cur = conn.cursor()


    cur.execute(
        """
        SELECT liquidity,
        volume,
        holders,
        result

        FROM learning

        WHERE result > 70
        """
    )


    winners = cur.fetchall()


    conn.close()



    if not winners:

        return 50



    best = 0



    for row in winners:


        old = {

            "liquidity": row[0],

            "volume": row[1],

            "holders": row[2]

        }


        match = similarity(
            current,
            old
        )


        if match > best:

            best = match



    return best
