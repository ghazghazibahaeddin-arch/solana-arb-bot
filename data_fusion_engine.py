"""
Ghost Engine Data Fusion

يجمع بيانات:
DexScreener
GeckoTerminal
Helius
Birdeye
Smart Money
"""

from birdeye_client import token_holders
from smart_money import analyze
from risk_engine import check


def safe_get(data, path, default=0):

    try:
        value = data

        for key in path:
            value = value[key]

        return value

    except Exception:
        return default



def build_token_profile(pair):


    symbol = safe_get(
        pair,
        ["baseToken", "symbol"],
        "UNKNOWN"
    )


    address = safe_get(
        pair,
        ["baseToken", "address"],
        ""
    )


    liquidity = safe_get(
        pair,
        ["liquidity","usd"],
        0
    )


    volume = safe_get(
        pair,
        ["volume","h24"],
        0
    )


    buys = safe_get(
        pair,
        ["txns","h24","buys"],
        0
    )


    sells = safe_get(
        pair,
        ["txns","h24","sells"],
        0
    )


    holders = 0

    try:

        holder_data = token_holders(address)

        holders = len(
            holder_data.get(
                "data",
                []
            )
        )

    except Exception:

        pass



    profile = {

        "symbol": symbol,

        "address": address,

        "liquidity": liquidity,

        "volume": volume,

        "buys": buys,

        "sells": sells,

        "holders": holders,


        "smart_money":
        analyze(pair),


        "pair":
        pair

    }


    return profile
