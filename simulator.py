# simulator.py

def simulate(pair):

    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume = pair.get("volume", {}).get("h24", 0)

    if liquidity == 0:
        return 0

    ratio = volume / liquidity

    return round(ratio, 2)
