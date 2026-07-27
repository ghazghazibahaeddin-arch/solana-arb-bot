"""
Ghost Engine - Decision Engine

Decision levels:

A+ = exceptional opportunity
A  = strong opportunity
B  = acceptable opportunity
C  = watch only
D  = reject

The engine never forces a trade just to reach a daily count.
"""

from typing import Any, Dict


# ============================================================
# CONFIG
# ============================================================

MAX_SCORE = 100.0

# Minimum score for an actual trade candidate.
TRADE_SCORE = 55.0

# Minimum score for a strong candidate.
STRONG_SCORE = 70.0

# Minimum score for exceptional candidate.
EXCEPTIONAL_SCORE = 85.0


# ============================================================
# HELPERS
# ============================================================

def number(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:

    return max(
        low,
        min(high, value),
    )


def extract_simulation(
    simulation: Any,
) -> Dict[str, Any]:

    if isinstance(
        simulation,
        dict,
    ):
        return simulation

    return {
        "expected_profit": number(
            simulation
        )
    }


def extract_profit(
    simulation: Any,
) -> float:

    data = extract_simulation(
        simulation
    )

    for key in (
        "expected_profit",
        "profit",
        "expected_return",
        "net_profit",
        "profit_percent",
    ):

        if key in data:

            return number(
                data[key]
            )

    return 0.0


def extract_risk(
    risk: Any,
) -> float:

    if isinstance(
        risk,
        bool,
    ):

        return 0.0 if risk else 100.0

    if isinstance(
        risk,
        dict,
    ):

        for key in (
            "risk_score",
            "risk",
            "danger",
        ):

            if key in risk:

                return clamp(
                    number(
                        risk[key]
                    )
                )

    return clamp(
        number(risk)
    )


def extract_smart_money(
    smart: Any,
) -> float:

    if isinstance(
        smart,
        dict,
    ):

        for key in (
            "score",
            "smart_money_score",
            "confidence",
        ):

            if key in smart:

                return clamp(
                    number(
                        smart[key]
                    )
                )

    return clamp(
        number(smart)
    )


def extract_pattern(
    pattern: Any,
) -> float:

    if isinstance(
        pattern,
        dict,
    ):

        for key in (
            "score",
            "pattern_score",
            "confidence",
        ):

            if key in pattern:

                return clamp(
                    number(
                        pattern[key]
                    )
                )

    return clamp(
        number(pattern)
    )


# ============================================================
# DECISION
# ============================================================

def decide(
    score: Any,
    risk: Any,
    simulation: Any,
    smart_money: Any,
    pattern: Any,
) -> Dict[str, Any]:

    base_score = clamp(
        number(score)
    )

    risk_score = extract_risk(
        risk
    )

    smart_score = extract_smart_money(
        smart_money
    )

    pattern_score = extract_pattern(
        pattern
    )

    expected_profit = extract_profit(
        simulation
    )

    # --------------------------------------------------------
    # Composite score
    # --------------------------------------------------------

    # Main score remains dominant.
    final_score = (
        base_score * 0.55
        + smart_score * 0.15
        + pattern_score * 0.15
        + (100.0 - risk_score) * 0.15
    )

    final_score = clamp(
        final_score
    )

    # --------------------------------------------------------
    # Hard safety conditions
    # --------------------------------------------------------

    if risk_score >= 80:

        return {
            "approved": False,
            "trade": False,
            "action": "REJECT",
            "level": "D",
            "score": round(
                final_score,
                2,
            ),
            "reason": "risk_too_high",
        }

    if expected_profit <= 0:

        return {
            "approved": False,
            "trade": False,
            "action": "REJECT",
            "level": "D",
            "score": round(
                final_score,
                2,
            ),
            "reason": "non_positive_simulation",
        }

    # --------------------------------------------------------
    # A+
    # --------------------------------------------------------

    if (
        final_score >= EXCEPTIONAL_SCORE
        and risk_score < 35
        and smart_score >= 60
        and pattern_score >= 60
    ):

        return {
            "approved": True,
            "trade": True,
            "action": "BUY",
            "level": "A+",
            "score": round(
                final_score,
                2,
            ),
            "reason": "exceptional_setup",
        }

    # --------------------------------------------------------
    # A
    # --------------------------------------------------------

    if (
        final_score >= STRONG_SCORE
        and risk_score < 50
        and (
            smart_score >= 40
            or pattern_score >= 50
        )
    ):

        return {
            "approved": True,
            "trade": True,
            "action": "BUY",
            "level": "A",
            "score": round(
                final_score,
                2,
            ),
            "reason": "strong_setup",
        }

    # --------------------------------------------------------
    # B
    # --------------------------------------------------------

    if (
        final_score >= TRADE_SCORE
        and risk_score < 65
    ):

        return {
            "approved": True,
            "trade": True,
            "action": "BUY",
            "level": "B",
            "score": round(
                final_score,
                2,
            ),
            "reason": "acceptable_setup",
        }

    # --------------------------------------------------------
    # C
    # --------------------------------------------------------

    if final_score >= 45:

        return {
            "approved": False,
            "trade": False,
            "action": "WATCH",
            "level": "C",
            "score": round(
                final_score,
                2,
            ),
            "reason": "watch_candidate",
        }

    # --------------------------------------------------------
    # D
    # --------------------------------------------------------

    return {
        "approved": False,
        "trade": False,
        "action": "REJECT",
        "level": "D",
        "score": round(
            final_score,
            2,
        ),
        "reason": "weak_setup",
        }
