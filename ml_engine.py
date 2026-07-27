import statistics

def average_score(results):

    scores=[]

    for pair in results:

        scores.append(pair["score"])

    if len(scores)==0:
        return 0

    return statistics.mean(scores)
