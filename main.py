"""
Ghost Engine Main

Live scanner
Risk
Fusion
Score
Simulation
Learning
"""


from scanner import live_scanner
from filters import filter_pairs

from data_fusion_engine import build_token_profile

from scorer import score_pair

from simulator import simulate

from learning_engine import (
    create_learning_table,
    save_prediction
)

from config import (
    MIN_SCORE,
    MAX_DAILY_TRADES
)



create_learning_table()



trade_count = 0



for pairs in live_scanner(2):


    pairs = filter_pairs(
        pairs
    )



    for pair in pairs:



        if trade_count >= MAX_DAILY_TRADES:

            print(
                "Daily limit reached"
            )

            break



        profile = build_token_profile(
            pair
        )


        score = score_pair(
            pair
        )


        simulation = simulate(
            pair
        )



        print("="*50)

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
            profile["smart_money"]
        )

        print(
            "SIMULATION:",
            simulation
        )



        save_prediction(

            profile["symbol"],

            profile["address"],

            score

        )



        if (

            score >= MIN_SCORE

            and

            simulation.get(
                "success",
                False
            )

        ):


            print(
                "🔥 OPPORTUNITY FOUND"
            )


            trade_count += 1
