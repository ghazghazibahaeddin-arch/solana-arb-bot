"""
Ghost Engine Risk Engine

Combines:
- Liquidity risk
- Volume anomaly
- Buy/Sell pressure
- Rug detector
- Holder distribution
- Dev wallet
"""

from config import MIN_LIQUIDITY

from rug_detector import detect_rug



def num(value):

    try:
        return float(value)

    except:
        return 0



def market_risk(pair):


    risk = 0

    reasons = []


    liquidity = num(
        pair.get(
            "liquidity",
            {}
        ).get(
            "usd",
            0
        )
    )


    volume = num(
        pair.get(
            "volume",
            {}
        ).get(
            "h24",
            0
        )
    )


    buys = num(
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
        )
    )


    sells = num(
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
    )


    # Liquidity

    if liquidity < MIN_LIQUIDITY:

        risk += 30

        reasons.append(
            "Low liquidity"
        )


    # Fake volume

    if liquidity > 0:

        ratio = volume / liquidity


        if ratio > 100:

            risk += 25

            reasons.append(
                "Possible fake volume"
            )


    # Sell pressure

    if sells > buys * 2:

        risk += 25

        reasons.append(
            "Heavy sell pressure"
        )



    # Transaction activity

    if buys + sells < 10:

        risk += 15

        reasons.append(
            "Low activity"
        )



    return {
        "risk": min(risk,100),
        "reasons": reasons
    }



def check(pair):


    result = market_risk(
        pair
    )


    rug = detect_rug(
        pair
    )


    final_risk = max(

        result["risk"],

        rug["rug_risk"]

    )


    print(
        "Risk:",
        final_risk
    )


    if final_risk >= 60:

        return False



    return True
