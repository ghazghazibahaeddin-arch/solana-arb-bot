def analyze(pair):

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


    volume = pair.get(
        "volume",
        {}
    ).get(
        "h24",
        0
    )


    score = 50



    if buys > sells:
        score += 20


    if volume > 0:

        ratio = buys / max(sells,1)

        if ratio > 2:
            score +=20



    return min(score,100)
