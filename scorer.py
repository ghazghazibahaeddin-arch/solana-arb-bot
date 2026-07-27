def score_pair(pair):

    score = 0

    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume = pair.get("volume", {}).get("h24", 0)

    buys = pair.get("txns", {}).get("h24", {}).get("buys", 0)
    sells = pair.get("txns", {}).get("h24", {}).get("sells", 0)

    if liquidity > 50000:
        score += 30

    if volume > 500000:
        score += 30

    if buys > sells:
        score += 20

    if volume > liquidity:
        score += 20

    return score
