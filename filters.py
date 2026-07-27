"""
Ghost Engine Filters

تنظيف قائمة العملات قبل إرسالها للمحرك
"""


from config import MIN_LIQUIDITY



def safe_number(value):

    try:
        return float(value)

    except:

        return 0



def filter_pairs(pairs):


    filtered = []


    for pair in pairs:


        try:


            # فقط Solana

            if pair.get(
                "chainId"
            ) != "solana":

                continue



            liquidity = safe_number(

                pair.get(
                    "liquidity",
                    {}
                ).get(
                    "usd",
                    0
                )

            )



            volume = safe_number(

                pair.get(
                    "volume",
                    {}
                ).get(
                    "h24",
                    0
                )

            )



            price = safe_number(

                pair.get(
                    "priceUsd",
                    0
                )

            )



            # تجاهل السيولة الضعيفة

            if liquidity < MIN_LIQUIDITY:

                continue



            # تجاهل العملات بلا حجم

            if volume <= 0:

                continue



            # تجاهل العملات بدون سعر

            if price <= 0:

                continue



            filtered.append(
                pair
            )



        except Exception:


            continue



    return filtered
