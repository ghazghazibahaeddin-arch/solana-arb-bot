# risk_engine.py

def check(pair):

    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume = pair.get("volume", {}).get("h24", 0)

    buys = pair.get("txns", {}).get("h24", {}).get("buys", 0)
    sells = pair.get("txns", {}).get("h24", {}).get("sells", 0)

    if liquidity < 30000:
        return False

    if volume < 100000:
        return False

    if sells > buys * 1.5:
        return False

    return True
