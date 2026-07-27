"""
Developer Wallet Tracker

تحليل نشاط المطور
"""

from helius_client import wallet_activity



def analyze_dev_wallet(wallet):


    if not wallet:


        return {

            "risk":50,

            "reason":
            "Unknown developer wallet"

        }



    try:


        txs = wallet_activity(
            wallet
        )


        transactions = (

            txs.get(
                "result",
                []
            )

        )



        count = len(
            transactions
        )



        if count > 100:


            return {

                "risk":20,

                "reason":
                "Active wallet"

            }




        if count < 5:


            return {

                "risk":70,

                "reason":
                "New suspicious wallet"

            }



        return {

            "risk":40,

            "reason":
            "Normal activity"

        }



    except Exception:


        return {

            "risk":60,

            "reason":
            "Wallet analysis failed"

          }
