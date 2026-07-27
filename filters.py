from config import MIN_LIQUIDITY, MIN_VOLUME

def filter_pairs(pairs):

    good = []

    for pair in pairs:

        liquidity = pair.get("liquidity", {}).get("usd", 0)

        volume = pair.get("volume", {}).get("h24", 0)

        if liquidity >= MIN_LIQUIDITY and volume >= MIN_VOLUME:
            good.append(pair)

    return good
