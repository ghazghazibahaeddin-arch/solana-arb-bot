"""
Ghost Intelligence Engine

Adaptive market intelligence layer.

Features:

- Token DNA
- Holder velocity
- Smart money gravity
- Volume quality
- Pattern matching
- Risk penalty
- Adaptive weights

This engine DOES NOT predict the future.
It estimates opportunity quality from live data.
"""


import math
import json
import os
from datetime import datetime



MEMORY_FILE = "ghost_memory.json"



DEFAULT_WEIGHTS = {


    "liquidity":
    0.15,


    "holder_velocity":
    0.20,


    "smart_money":
    0.20,


    "volume_quality":
    0.15,


    "pattern":
    0.15,


    "activity":
    0.15

}




def load_memory():

    try:

        with open(
            MEMORY_FILE,
            "r"
        ) as f:

            return json.load(f)


    except:

        return {

            "wins":0,

            "losses":0,

            "weights":
            DEFAULT_WEIGHTS

        }





def save_memory(data):


    with open(
        MEMORY_FILE,
        "w"
    ) as f:

        json.dump(

            data,

            f,

            indent=4

        )





# -------------------------
# Token DNA
# -------------------------


def token_dna(pair):


    liquidity = float(

        pair.get(
            "liquidity",
            {}
        ).get(
            "usd",
            0
        )

    )


    volume = float(

        pair.get(
            "volume",
            {}
        ).get(
            "h24",
            0
        )

    )



    buys = (

        pair.get(
            "txns",
            {}
        )
        .get(
            "h24",
            {}
        )
        .get(
            "buys",
            0
        )

    )



    sells = (

        pair.get(
            "txns",
            {}
        )
        .get(
            "h24",
            {}
        )
        .get(
            "sells",
            0
        )

    )



    return {


        "liquidity":

        liquidity,


        "volume":

        volume,


        "buy_pressure":

        buys /
        max(
            sells,
            1
        )

    }





# -------------------------
# Holder Velocity
# -------------------------


def holder_velocity(
    old_holders,
    new_holders,
    minutes
):


    if minutes <=0:

        return 0



    growth = (

        new_holders
        -
        old_holders

    )


    velocity = (

        growth /
        minutes

    )


    return min(

        velocity * 10,

        100

    )





# -------------------------
# Smart Money Gravity
# -------------------------


def smart_money_gravity(
    wallets
):


    if not wallets:

        return 0



    total = 0



    for wallet in wallets:


        total += wallet.get(

            "performance_score",

            0

        )



    return min(

        total /
        len(wallets),

        100

    )





# -------------------------
# Real Volume
# -------------------------


def volume_quality(
    volume,
    buyers,
    holders
):


    if volume <=0:

        return 0



    score = (

        buyers
        *
        holders

    ) / volume



    return min(

        math.log1p(
            score
        )
        *
        20,

        100

    )





# -------------------------
# Main Intelligence
# -------------------------


def analyze(

    pair,

    old_holders=0,

    new_holders=0,

    minutes=60,

    smart_wallets=None,

    pattern_score=0

):


    memory = load_memory()

    weights = memory["weights"]



    dna = token_dna(pair)



    liquidity_score = min(

        dna["liquidity"]
        /
        50000
        *
        100,

        100

    )



    velocity = holder_velocity(

        old_holders,

        new_holders,

        minutes

    )



    smart = smart_money_gravity(

        smart_wallets or []

    )



    volume = volume_quality(

        dna["volume"],

        dna.get(
            "buyers",
            1
        ),

        new_holders

    )



    activity = min(

        dna["buy_pressure"]
        *
        20,

        100

    )



    score=(

        liquidity_score
        *
        weights["liquidity"]


        +

        velocity
        *
        weights["holder_velocity"]


        +

        smart
        *
        weights["smart_money"]


        +

        volume
        *
        weights["volume_quality"]


        +

        pattern_score
        *
        weights["pattern"]


        +

        activity
        *
        weights["activity"]

    )



    return {


        "ghost_score":

        round(
            score,
            2
        ),


        "dna":

        dna,


        "timestamp":

        str(
            datetime.utcnow()
        )

    }





# -------------------------
# Learning
# -------------------------


def update_result(
    result
):


    memory = load_memory()


    if result=="win":

        memory["wins"] +=1


    else:

        memory["losses"] +=1



    # تعديل بسيط للأوزان

    total=(

        memory["wins"]

        +

        memory["losses"]

    )


    if total > 100:


        winrate = (

            memory["wins"]

            /

            total

        )


        if winrate < 0.4:


            memory["weights"][

            "risk"

            ] = 0.3



    save_memory(
        memory
)
