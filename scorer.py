from pattern_detector import detect_pattern
from smart_money import analyze



def score_pair(pair):


    score = 0



    liquidity = pair.get(
        "liquidity",
        {}
    ).get(
        "usd",
        0
    )



    volume = pair.get(
        "volume",
        {}
    ).get(
        "h24",
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



    # Liquidity

    if liquidity > 100000:
        score +=25

    elif liquidity > 30000:
        score +=15



    # Volume

    if volume > 1000000:
        score +=25

    elif volume > 300000:
        score +=15



    # Buyers

    if buys > sells:
        score +=15



    # Volume / liquidity

    if liquidity > 0:

        ratio = volume/liquidity

        if ratio > 3:
            score +=15



    smart = analyze(pair)

    score += smart * 0.1



    pattern = detect_pattern(pair)

    score += pattern * 0.1



    return round(
        min(score,100),
        2
    )
