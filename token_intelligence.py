from social_signal import analyze_social
from smart_money import analyze
from pattern_detector import detect_pattern



def intelligence(pair):


    smart = analyze(pair)

    social = analyze_social(
        pair.get(
        "baseToken",
        {})
        .get(
        "symbol",
        "")
    )


    pattern = detect_pattern(pair)



    final = (

        smart*0.4 +

        social*0.3 +

        pattern*0.3

    )


    return {

        "smart_money":smart,

        "social":social,

        "pattern":pattern,

        "total":
        round(final,2)

  }
