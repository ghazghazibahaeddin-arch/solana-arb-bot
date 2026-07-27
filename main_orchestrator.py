"""
Ghost Engine Main Orchestrator

Pipeline:

Scanner
 ↓
Filters
 ↓
Risk
 ↓
Fusion
 ↓
Smart Money
 ↓
Pattern
 ↓
Score
 ↓
Simulator
 ↓
Decision
 ↓
Learning

Includes:
- Error recovery
- Logging
- Auto retry
"""


import time
import traceback
import logging


from scanner import fetch_pairs

from filters import filter_pairs

from risk_engine import check

from data_fusion_engine import build_token_profile

from scorer import score_pair

from simulator import simulate

from decision_engine import decide

from smart_wallet_tracker import analyze as smart_analyze

from pattern_detector import detect_pattern

from learning_engine import (
    create_learning_table,
    save_prediction
)



# -----------------------
# Logging
# -----------------------

logging.basicConfig(

    filename="ghost_engine.log",

    level=logging.INFO,

    format="%(asctime)s %(message)s"

)



# -----------------------
# Settings
# -----------------------

SCAN_DELAY = 3

MAX_ERRORS = 5



def safe_run(function,*args):

    """
    يمنع توقف النظام
    إذا فشل ملف معين
    """

    try:

        return function(*args)


    except Exception as e:


        logging.error(

            f"{function.__name__}: {e}"

        )


        traceback.print_exc()


        return None





def process_pair(pair):


    try:


        # 1 Risk

        if not check(pair):

            return



        # 2 Fusion

        profile = safe_run(

            build_token_profile,

            pair

        )


        if not profile:

            return



        # 3 Score

        score = safe_run(

            score_pair,

            pair

        )


        if score is None:

            return




        # 4 Simulation

        simulation = safe_run(

            simulate,

            pair

        )


        if not simulation:

            return




        # 5 Smart Money

        smart = safe_run(

            smart_analyze,

            pair

        )



        if smart is None:

            smart = 0




        # 6 Pattern

        pattern = safe_run(

            detect_pattern,

            pair

        )


        if pattern is None:

            pattern = 0





        # 7 Decision

        decision = decide(

            score,

            0,

            simulation,

            smart,

            pattern

        )





        print("="*60)

        print(

            "TOKEN:",

            profile["symbol"]

        )


        print(

            "SCORE:",

            score

        )


        print(

            "SMART MONEY:",

            smart

        )


        print(

            "PATTERN:",

            pattern

        )


        print(

            "DECISION:",

            decision

        )





        # Learning

        save_prediction(

            profile["symbol"],

            profile["address"],

            score

        )



    except Exception as e:


        logging.error(

            f"PAIR ERROR {e}"

        )





def start():


    create_learning_table()


    errors = 0



    while True:


        try:


            print(
                "Scanning..."
            )


            pairs = fetch_pairs()



            if not pairs:


                time.sleep(
                    SCAN_DELAY
                )

                continue




            pairs = filter_pairs(
                pairs
            )



            for pair in pairs:


                process_pair(
                    pair
                )



            errors = 0



            time.sleep(
                SCAN_DELAY
            )



        except Exception as e:


            errors += 1


            logging.error(
                f"MAIN LOOP ERROR {e}"
            )



            if errors >= MAX_ERRORS:


                print(
                    "Too many errors. Restart needed."
                )


                break



            time.sleep(
                5
            )





if __name__ == "__main__":


    start()
