"""
Ghost Engine Decision Engine

يجمع:
- Score
- Risk
- Simulation
- Pattern
- Smart Money

ويقرر:
IGNORE
WATCH
PAPER BUY
"""


from config import MIN_SCORE



def decide(
    score,
    risk,
    simulation,
    smart_money=0,
    pattern=0
):


    # خطر عالي

    if risk >= 60:

        return {

            "decision":
            "IGNORE",

            "reason":
            "High risk"

        }



    # Simulation فاشل

    if not simulation.get(
        "success",
        False
    ):

        return {

            "decision":
            "IGNORE",

            "reason":
            "Bad simulation"

        }



    # Score ضعيف

    if score < MIN_SCORE:


        return {

            "decision":
            "WATCH",

            "reason":
            "Score below threshold"

        }



    confidence = (

        score * 0.5

        +

        smart_money * 0.25

        +

        pattern * 0.25

    )



    if confidence >= 85:


        return {


            "decision":
            "PAPER_BUY",


            "confidence":
            round(
                confidence,
                2
            ),


            "reason":
            "Strong combined signals"

        }



    return {


        "decision":
        "WATCH",


        "confidence":
        round(
            confidence,
            2
        )

    }
