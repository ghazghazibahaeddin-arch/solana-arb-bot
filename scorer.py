"""
Ghost Engine Scoring System

Input:
    Unified token data from:
    - DexScreener
    - GeckoTerminal
    - Helius
    - Birdeye
    - Learning Engine
    - Smart Wallet Tracker

Output:
    Score 0-100
"""


from smart_wallet_tracker import smart_wallet_score
from learning_engine import prediction_score



def clamp(value, minimum=0, maximum=100):

    return max(
        minimum,
        min(
            value,
            maximum
        )
    )



def normalize(value, max_value):

    if max_value <= 0:
        return 0

    return clamp(
        (value / max_value) * 100
    )



def calculate_buy_pressure(
        buys,
        sells
):

    if sells == 0:

        if buys > 0:
            return 100

        return 0


    ratio = buys / sells


    return clamp(
        ratio * 50
    )



def score_pair(pair):


    # -------------------------
    # DexScreener Data
    # -------------------------

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


    txns = pair.get(
        "txns",
        {}
    ).get(
        "h24",
        {}
    )


    buys = txns.get(
        "buys",
        0
    )


    sells = txns.get(
        "sells",
        0
    )


    # -------------------------
    # Basic Market Signals
    # -------------------------

    liquidity_score = normalize(
        liquidity,
        200000
    )


    volume_score = normalize(
        volume,
        1000000
    )


    buy_pressure = calculate_buy_pressure(
        buys,
        sells
    )


    # -------------------------
    # Smart Money
    # -------------------------

    try:

        smart_score = smart_wallet_score(
            pair
        )

    except Exception:

        smart_score = 0



    # -------------------------
    # Historical Learning
    # -------------------------

    try:

        history_score = prediction_score(
            pair
        )

    except Exception:

        history_score = 0



    # -------------------------
    # Final Weighted Score
    # -------------------------

    final_score = (

        liquidity_score * 0.25 +

        volume_score * 0.25 +

        buy_pressure * 0.20 +

        smart_score * 0.15 +

        history_score * 0.15

    )


    return round(
        clamp(final_score),
        2
    )



def should_trade(
        score,
        minimum=85
):

    """
    Entry filter.
    لا يعني ضمان الربح.
    """

    return score >= minimum
