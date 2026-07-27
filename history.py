from database import connect

def save_token(pair):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""

    INSERT INTO tokens(

    symbol,
    address,
    price,
    liquidity,
    volume,
    score

    )

    VALUES(?,?,?,?,?,?)

    """,(

    pair["baseToken"]["symbol"],
    pair["baseToken"]["address"],
    float(pair["priceUsd"]),
    pair["liquidity"]["usd"],
    pair["volume"]["h24"],
    pair["score"]

    ))

    conn.commit()
    conn.close()
