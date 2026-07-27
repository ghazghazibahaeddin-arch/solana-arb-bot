"""
Holder Distribution Analyzer

يكشف تركيز الملكية
"""



def calculate_holder_risk(holders):

    """
    holders:
    [
      {
        "address":"",
        "percentage":20
      }
    ]
    """

    if not holders:

        return {
            "risk":50,
            "reason":"No holder data"
        }



    top10 = sorted(

        holders,

        key=lambda x:
        x.get(
            "percentage",
            0
        ),

        reverse=True

    )[:10]



    concentration = sum(

        h.get(
            "percentage",
            0
        )

        for h in top10

    )



    if concentration > 80:

        return {

            "risk":90,

            "reason":
            "Top 10 holders own too much"

        }



    if concentration > 60:

        return {

            "risk":60,

            "reason":
            "High holder concentration"

        }



    return {

        "risk":20,

        "reason":
        "Healthy distribution"

    }




def analyze_holders(data):


    return calculate_holder_risk(
        data
      )
