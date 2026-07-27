from scanner import live_scanner
from filters import filter_pairs
from scorer import score_pair
from risk_engine import check
from ai_brain import analyze_token


MAX_TRADES = 1000

trade_count = 0



for pairs in live_scanner(2):


    if trade_count >= MAX_TRADES:

        print("Daily limit reached")

        break



    pairs = filter_pairs(pairs)



    for pair in pairs:


        if not check(pair):

            continue



        score = score_pair(pair)



        if score < 85:

            continue



        ai = analyze_token(pair)



        print(
            pair["baseToken"]["symbol"],
            score,
            ai
        )



        # هنا فقط بعد simulator + wallet

        # execute_trade(pair)

        trade_count +=1
