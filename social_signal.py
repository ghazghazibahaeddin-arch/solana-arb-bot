import requests



def analyze_social(symbol):


    score = 0


    # لاحقا تربطه بـ APIs حقيقية


    keywords=[
        "moon",
        "gem",
        "100x",
        "solana"
    ]


    text=symbol.lower()



    for word in keywords:

        if word in text:

            score +=20



    return min(score,100)
