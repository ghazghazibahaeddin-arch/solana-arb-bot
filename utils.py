def usd(value):

    try:
        return "${:,.2f}".format(float(value))
    except:
        return "$0"
