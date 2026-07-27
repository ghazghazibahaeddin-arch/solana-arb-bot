import random


def simulate(pair):

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


    if liquidity == 0:
        return {
            "success":False,
            "reason":"No liquidity"
        }


    volume_ratio = volume / liquidity


    slippage = random.uniform(
        0.5,
        5
    )


    expected_move = volume_ratio * 10


    profit = expected_move - slippage



    return {

        "success":
        profit > 5,

        "expected_profit":
        round(profit,2),

        "slippage":
        round(slippage,2)

    }
