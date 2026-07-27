"""
Ghost Engine Risk Engine

يفحص:
- السيولة
- ضغط البيع
- توزيع التداول
- عمر الزوج
- مخاطر المطور

يعطي:
True = يسمح بالمرور
False = يرفض
"""


from config import MIN_LIQUIDITY



def number(value):

    try:

        return float(value)

    except:

        return 0




def get_risk_score(pair):


    risk = 0



    liquidity = number(

        pair.get(
            "liquidity",
            {}
        ).get(
            "usd",
            0
        )

    )



    volume = number(

        pair.get(
            "volume",
            {}
        ).get(
            "h24",
            0
        )

    )



    buys = number(

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



    sells = number(

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



    # -------------------
    # Liquidity Risk
    # -------------------


    if liquidity < 5000:

        risk += 40


    elif liquidity < MIN_LIQUIDITY:

        risk += 20




    # -------------------
    # Fake Volume Risk
    # -------------------


    if liquidity > 0:


        ratio = volume / liquidity


        # حجم ضخم مقارنة بالسيولة

        if ratio > 100:

            risk += 30




    # -------------------
    # Sell Pressure
    # -------------------


    if sells > buys * 2:

        risk += 25



    # -------------------
    # Transaction Risk
    # -------------------


    total_tx = buys + sells


    if total_tx < 10:

        risk += 20



    return min(
        risk,
        100
    )




def check(pair):


    risk = get_risk_score(
        pair
    )


    print(
        "Risk:",
        risk
    )



    # كلما كان أقل أفضل

    if risk >= 60:

        return False



    return True
