from market_memory import get_success_patterns



def detect_pattern(pair):

    history = get_success_patterns()

    if not history:
        return 50


    liquidity = pair.get("liquidity",{}).get("usd",0)
    volume = pair.get("volume",{}).get("h24",0)


    matches = 0


    for token in history:

        old_liquidity = token[3]
        old_volume = token[4]


        if old_liquidity == 0:
            continue


        liquidity_difference = abs(
            liquidity-old_liquidity
        ) / old_liquidity


        volume_difference = abs(
            volume-old_volume
        ) / old_volume


        if liquidity_difference < 0.5:
            matches += 1


        if volume_difference < 0.5:
            matches += 1



    score = min(matches * 5,100)


    return score
