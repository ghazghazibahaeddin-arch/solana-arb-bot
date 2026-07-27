import time


MAX_TRADES = 1000

trades_today = 0


def can_trade():

    global trades_today


    if trades_today >= MAX_TRADES:

        return False


    return True



def register_trade():

    global trades_today

    trades_today +=1



def status():

    return trades_today
