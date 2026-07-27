"""
Ghost Engine Main

Pipeline:

DexScreener Scanner
        |
        v
Filters
        |
        v
Risk Engine
        |
        v
Data Fusion
        |
        v
Smart Money
        |
        v
Pattern Detection
        |
        v
Scoring
        |
        v
Simulation
        |
        v
Decision
        |
        v
Learning Database
"""


import time
import logging


from scanner import fetch_pairs

from filters import filter_pairs

from risk_engine import check

from data_fusion_engine import build_token_profile

from scorer import score_pair

from simulator import simulate

from smart_wallet_tracker import analyze as smart_money

from pattern_detector import detect_pattern

from decision_engine import decide

from learning_engine import (
    create_learning_table,
    save_prediction
)


# ==========================
# SETTINGS
# ==========================

SCAN_INTERVAL = 3


logging.basicConfig(

    filename="ghost_engine.log",

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)



# ==========================
# SAFE EXECUTION
# ==========================


def safe_call(func, *args):

    try:

        return func(*args)


    except Exception as e:


        logging.error(

            f"{func.__name__} ERROR: {e}"

        )


        return None




# ==========================
# PROCESS TOKEN
# ==========================


def analyze_token(pair):


    try:


        # 1- Risk Check

        if not check(pair):

            return None



        # 2- Combine data

        profile = safe_call(

            build_token_profile,

            pair

        )


        if not profile:

            return None




        # 3- Score

        score = safe_call(

            score_pair,

            pair

        )


        if score is None:

            return None




        # 4- Simulation

        simulation = safe_call(

            simulate,

            pair

        )


        if not simulation:

            return None




        # 5- Smart money

        smart = safe_call(

            smart_money,

            pair

        )


        if smart is None:

            smart = 0




        # 6- Pattern

        pattern = safe_call(

            detect_pattern,

            pair

        )


        if pattern is None:

            pattern = 0




        # 7- Decision

        decision = decide(

            score,

            0,

            simulation,

            smart,

            pattern

        )




        result = {


            "symbol":

            profile.get(
                "symbol"
            ),


            "address":

            profile.get(
                "address"
            ),


            "score":

            score,


            "smart_money":

            smart,


            "pattern":

            pattern,


            "simulation":

            simulation,


            "decision":

            decision

        }




        return result



    except Exception as e:


        logging.error(

            f"TOKEN ERROR: {e}"

        )


        return None




# ==========================
# MAIN LOOP
# ==========================


def main():


    print(
        "👻 Ghost Engine Started"
    )


    create_learning_table()



    while True:


        try:


            print(
                "\nScanning..."
            )


            pairs = fetch_pairs()



            if not pairs:


                print(
                    "No data"
                )


                time.sleep(
                    SCAN_INTERVAL
                )


                continue




            pairs = filter_pairs(
                pairs
            )



            opportunities = []



            for pair in pairs:


                result = analyze_token(
                    pair
                )


                if result:


                    opportunities.append(
                        result
                    )




                    save_prediction(

                        result["symbol"],

                        result["address"],

                        result["score"]

                    )






            opportunities.sort(

                key=lambda x:
                x["score"],

                reverse=True

            )





            for item in opportunities[:10]:


                print(
                    "\n--------------------"
                )


                print(
                    "TOKEN:",
                    item["symbol"]
                )


                print(
                    "SCORE:",
                    item["score"]
                )


                print(
                    "SMART:",
                    item["smart_money"]
                )


                print(
                    "PATTERN:",
                    item["pattern"]
                )


                print(
                    "DECISION:",
                    item["decision"]
                )





            time.sleep(
                SCAN_INTERVAL
            )



        except KeyboardInterrupt:


            print(
                "Stopped"
            )


            break




        except Exception as e:


            logging.error(

                f"MAIN LOOP ERROR: {e}"

            )


            time.sleep(
                5
            )





if __name__ == "__main__":

    main()
