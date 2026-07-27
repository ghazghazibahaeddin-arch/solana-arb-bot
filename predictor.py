def predict(pair):

    score = pair["score"]

    if score >= 90:
        return "VERY STRONG"

    if score >= 75:
        return "GOOD"

    if score >= 60:
        return "WATCH"

    return "IGNORE"
