def filter_pairs(pairs):

    good = []


    for pair in pairs:


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


        price = pair.get(
            "priceUsd",
            0
        )


        if not price:
            continue


        if liquidity < 10000:
            continue


        if volume < 20000:
            continue


        good.append(pair)



    return good
