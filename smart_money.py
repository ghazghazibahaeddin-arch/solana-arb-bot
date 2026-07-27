# smart_money.py

def analyze(pair):

    buys = pair.get("txns", {}).get("h24", {}).get("buys", 0)
    sells = pair.get("txns", {}).get("h24", {}).get("sells", 0)

    if buys > sells * 2:
        return "Strong Buying"

    if sells > buys * 2:
        return "Heavy Selling"

    return "Neutral"
