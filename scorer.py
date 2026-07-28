"""
Ghost Engine Scoring System (FIXED)

Input:
Unified token data from:
- DexScreener
- GeckoTerminal
- Helius
- Birdeye
- Learning Engine
- Smart Wallet Tracker

Output:
Score 0-100

Original bug: smart_wallet_score(pair) and prediction_score(pair)
are both designed to return 50 (neutral/unknown) when there's no
data. But scorer.py wrapped them in try/except and defaulted to 0
on ANY exception -- so a genuine bug (network error, missing key,
etc.) silently became "worst possible score" instead of "unknown",
unfairly tanking a token's score for reasons that have nothing to
do with the token itself.

Fix: default to 50 (neutral) on exception, matching the modules'
own "no data" convention, and log the exception so real bugs are
visible instead of silently hidden as a bad score.
"""

import logging

from smart_wallet_tracker import smart_wallet_score
from learning_engine import prediction_score

logger = logging.getLogger("scorer")


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(value, maximum))


def normalize(value, max_value):
    if max_value <= 0:
        return 0
    return clamp((value / max_value) * 100)


def calculate_buy_pressure(buys, sells):
    if sells == 0:
        return 100 if buys > 0 else 0
    ratio = buys / sells
    return clamp(ratio * 50)


def score_pair(pair):
    # -------------------------
    # DexScreener Data
    # -------------------------
    liquidity = pair.get("liquidity", {}).get("usd", 0)
    volume = pair.get("volume", {}).get("h24", 0)
    txns = pair.get("txns", {}).get("h24", {})
    buys = txns.get("buys", 0)
    sells = txns.get("sells", 0)

    # -------------------------
    # Basic Market Signals
    # -------------------------
    liquidity_score = normalize(liquidity, 200000)
    volume_score = normalize(volume, 1000000)
    buy_pressure = calculate_buy_pressure(buys, sells)

    # -------------------------
    # Smart Money
    # NOTE: default is 50 (neutral), not 0. A real exception here
    # is a bug worth knowing about -- it's logged, not hidden.
    # -------------------------
    try:
        smart_score = smart_wallet_score(pair)
    except Exception:
        logger.exception("smart_wallet_score failed; using neutral 50")
        smart_score = 50

    # -------------------------
    # Historical Learning
    # Same fix: neutral default, not a punishing 0.
    # -------------------------
    try:
        history_score = prediction_score(pair)
    except Exception:
        logger.exception("prediction_score failed; using neutral 50")
        history_score = 50

    # -------------------------
    # Final Weighted Score
    # -------------------------
    final_score = (
        liquidity_score * 0.25
        + volume_score * 0.25
        + buy_pressure * 0.20
        + smart_score * 0.15
        + history_score * 0.15
    )

    return round(clamp(final_score), 2)


def should_trade(score, minimum=55):
    """
    Entry filter. NOTE: default changed from 85 to 55 to match
    decision_engine.TRADE_SCORE / config.MIN_SCORE. This function
    isn't currently called anywhere in main.py's pipeline (score
    is compared directly against MIN_SCORE there), but keeping its
    default consistent avoids confusion if it's wired in later.

    لا يعني ضمان الربح.
    """
    return score >= minimum
