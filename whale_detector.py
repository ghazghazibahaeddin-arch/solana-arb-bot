# whale_detector.py

def detect(pair):

    volume = pair.get("volume", {}).get("h24", 0)

    if volume > 1000000:
        return True

    return False
