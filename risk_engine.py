def check(pair):


    risk = 100



    liquidity = pair.get(
        "liquidity",
        {}
    ).get(
        "usd",
        0
    )


    buys = pair.get(
        "txns",
        {}
    ).get(
        "h24",
        {}
    ).get(
        "buys",
        0
    )


    sells = pair.get(
        "txns",
        {}
    ).get(
        "h24",
        {}
    ).get(
        "sells",
        0
    )


    # liquidity danger

    if liquidity < 10000:

        risk -=40



    # selling pressure

    if sells > buys:

        risk -=30



    # too few buyers

    if buys < 20:

        risk -=20



    return risk >= 60
