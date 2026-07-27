"""
Ghost Engine Trade Simulator

يحاول معرفة:
- هل الدخول منطقي؟
- تأثير السيولة
- الانزلاق المتوقع
- الربح المحتمل

لا ينفذ أي صفقة.
"""


def safe_number(value):

    try:

        return float(value)

    except:

        return 0




def simulate(pair):


    liquidity = safe_number(

        pair.get(
            "liquidity",
            {}
        ).get(
            "usd",
            0
        )

    )


    volume = safe_number(

        pair.get(
            "volume",
            {}
        ).get(
            "h24",
            0
        )

    )


    buys = safe_number(

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


    sells = safe_number(

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


    # --------------------
    # حماية السيولة
    # --------------------

    if liquidity < 5000:


        return {

            "success": False,

            "reason":
            "Low liquidity"

        }



    # --------------------
    # ضغط الشراء
    # --------------------

    if sells == 0:

        buy_pressure = 100

    else:

        buy_pressure = (
            buys /
            sells
        ) * 100



    # --------------------
    # نسبة التداول للسيولة
    # --------------------

    volume_ratio = (
        volume /
        liquidity
    )



    # --------------------
    # تقدير الحركة
    # --------------------

    momentum = (

        volume_ratio * 20

        +

        buy_pressure * 0.3

    )



    # --------------------
    # Slippage تقريبي
    # --------------------

    if liquidity > 100000:

        slippage = 0.5


    elif liquidity > 20000:

        slippage = 1.5


    else:

        slippage = 3




    expected_profit = (

        momentum

        -

        slippage

    )



    success = (

        expected_profit > 5

        and

        buy_pressure > 120

    )



    return {


        "success":
        success,


        "expected_profit_percent":
        round(
            expected_profit,
            2
        ),


        "buy_pressure":
        round(
            buy_pressure,
            2
        ),


        "slippage":
        slippage,


        "liquidity":
        liquidity,


        "volume":
        volume

    }
