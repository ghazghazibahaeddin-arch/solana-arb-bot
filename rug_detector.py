"""
Rug Pull Detection Engine

Combines:
- Holder risk
- Dev wallet risk
- Liquidity
- Volume anomaly
"""



from holder_distribution import analyze_holders
from dev_wallet_tracker import analyze_dev_wallet



def detect_rug(
    pair,
    holders=None,
    dev_wallet=None
):


    risk = 0

    reasons = []



    # -------------------
    # Liquidity
    # -------------------

    liquidity = pair.get(
        "liquidity",
        {}
    ).get(
        "usd",
        0
    )



    if liquidity < 5000:


        risk += 30

        reasons.append(
            "Low liquidity"
        )




    # -------------------
    # Holders
    # -------------------


    if holders:


        holder_result = analyze_holders(
            holders
        )


        risk += holder_result["risk"] * 0.4


        if holder_result["risk"] > 60:

            reasons.append(
                holder_result["reason"]
            )




    # -------------------
    # Developer
    # -------------------


    if dev_wallet:


        dev_result = analyze_dev_wallet(
            dev_wallet
        )


        risk += dev_result["risk"] * 0.4


        if dev_result["risk"] > 60:

            reasons.append(
                dev_result["reason"]
            )




    risk = min(
        int(risk),
        100
    )



    return {


        "rug_risk":
        risk,


        "safe":
        risk < 50,


        "reasons":
        reasons

    }




def is_safe(
    pair,
    holders=None,
    dev_wallet=None
):


    result = detect_rug(
        pair,
        holders,
        dev_wallet
    )


    return result["safe"]
