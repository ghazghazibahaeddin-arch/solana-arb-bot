"""
Ghost Engine - Main Orchestrator

Live pipeline:

Scanner
   ↓
Filters
   ↓
Risk
   ↓
Data Fusion
   ↓
Smart Money
   ↓
Pattern Detection
   ↓
Scoring
   ↓
Simulation
   ↓
Decision
   ↓
Learning

The engine scans continuously.

It does NOT force 10 trades/day.
It can execute up to MAX_DAILY_TRADES when genuine
opportunities are detected.

Default:
    scan every 3 seconds
    maximum 50 trades/day
    paper mode

IMPORTANT:
This file only decides whether an opportunity is tradeable.
Actual live execution must be handled by trade_manager.py.
"""

import json
import logging
import os
import time

from datetime import datetime, date
from typing import Any, Dict, List, Optional


# ============================================================
# MODULES
# ============================================================

from scanner import fetch_pairs
from filters import filter_pairs
from risk_engine import check
from data_fusion_engine import build_token_profile
from scorer import score_pair
from simulator import simulate

from smart_wallet_tracker import (
    analyze as smart_money,
)

from pattern_detector import (
    detect_pattern,
)

from decision_engine import (
    decide,
)

from learning_engine import (
    create_learning_table,
    save_prediction,
)


# ============================================================
# OPTIONAL NETWORK GUARD
# ============================================================

try:

    from network_guard import check_all

except ImportError:

    check_all = None


# ============================================================
# CONFIG
# ============================================================

SCAN_INTERVAL = float(
    os.getenv(
        "SCAN_INTERVAL",
        "3",
    )
)

ERROR_RETRY_INTERVAL = float(
    os.getenv(
        "ERROR_RETRY_INTERVAL",
        "10",
    )
)

MAX_PAIRS_PER_CYCLE = int(
    os.getenv(
        "MAX_PAIRS_PER_CYCLE",
        "250",
    )
)

MAX_DAILY_TRADES = int(
    os.getenv(
        "MAX_DAILY_TRADES",
        "50",
    )
)

MIN_SCORE = float(
    os.getenv(
        "MIN_SCORE",
        "45",
    )
)

RUN_MODE = os.getenv(
    "RUN_MODE",
    "paper",
).lower()

STATE_FILE = "state.json"

LOG_FILE = "ghost_engine.log"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "ghost_engine"
)


# ============================================================
# STATE
# ============================================================

def default_state() -> Dict[str, Any]:

    return {
        "date": str(date.today()),
        "daily_trades": 0,
        "scan_count": 0,
        "errors": 0,
        "last_scan": 0,
        "last_successful_scan": 0,
        "last_error": None,
    }


def load_state() -> Dict[str, Any]:

    state = default_state()

    if not os.path.exists(
        STATE_FILE
    ):

        return state

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            loaded = json.load(
                file
            )

        if isinstance(
            loaded,
            dict,
        ):

            state.update(
                loaded
            )

    except Exception as error:

        logger.error(
            "STATE LOAD ERROR: %s",
            error,
        )

    # New day.
    today = str(
        date.today()
    )

    if state.get(
        "date"
    ) != today:

        state = default_state()

    return state


def save_state(
    state: Dict[str, Any],
) -> None:

    temporary = (
        STATE_FILE
        + ".tmp"
    )

    try:

        with open(
            temporary,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                state,
                file,
                indent=2,
            )

            file.flush()

        os.replace(
            temporary,
            STATE_FILE,
        )

    except Exception as error:

        logger.error(
            "STATE SAVE ERROR: %s",
            error,
        )


# ============================================================
# HELPERS
# ============================================================

def safe_call(
    func,
    *args,
    default=None,
    name="module",
):

    try:

        return func(
            *args
        )

    except Exception as error:

        logger.exception(
            "%s ERROR: %s",
            name,
            error,
        )

        return default


def get_number(
    value: Any,
    default: float = 0,
) -> float:

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def extract_score(
    value: Any,
) -> Optional[float]:

    if isinstance(
        value,
        (int, float),
    ):

        return float(
            value
        )

    if isinstance(
        value,
        dict,
    ):

        for key in (
            "score",
            "total_score",
            "final_score",
        ):

            if key in value:

                return get_number(
                    value[key],
                    None,
                )

    return None


def valid_pair(
    pair: Any,
) -> bool:

    if not isinstance(
        pair,
        dict,
    ):
        return False

    base = pair.get(
        "baseToken"
    )

    if not isinstance(
        base,
        dict,
    ):
        return False

    if not base.get(
        "address"
    ):
        return False

    if not base.get(
        "symbol"
    ):
        return False

    return True


# ============================================================
# NETWORK
# ============================================================

def network_ok() -> bool:

    if check_all is None:

        # Do not block the entire scanner if the optional
        # network guard module is not installed.
        return True

    try:

        result = check_all()

        if isinstance(
            result,
            bool,
        ):

            return result

        if isinstance(
            result,
            dict,
        ):

            return bool(
                result.get(
                    "healthy",
                    False,
                )
            )

        return False

    except Exception as error:

        logger.error(
            "NETWORK ERROR: %s",
            error,
        )

        return False


# ============================================================
# DAILY TRADE LIMIT
# ============================================================

def trade_limit_reached(
    state: Dict[str, Any],
) -> bool:

    return (
        int(
            state.get(
                "daily_trades",
                0,
            )
        )
        >= MAX_DAILY_TRADES
    )


# ============================================================
# ANALYZE TOKEN
# ============================================================

def analyze_token(
    pair: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not valid_pair(
        pair
    ):

        return None

    base = pair[
        "baseToken"
    ]

    symbol = base.get(
        "symbol",
        "UNKNOWN",
    )

    address = base.get(
        "address"
    )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk = safe_call(
        check,
        pair,
        default=False,
        name="risk_engine",
    )

    if not risk:

        return None

    # --------------------------------------------------------
    # DATA FUSION
    # --------------------------------------------------------

    profile = safe_call(
        build_token_profile,
        pair,
        default=None,
        name="data_fusion",
    )

    if not isinstance(
        profile,
        dict,
    ):

        return None

    # --------------------------------------------------------
    # SMART MONEY
    # --------------------------------------------------------

    smart = safe_call(
        smart_money,
        pair,
        default=0,
        name="smart_money",
    )

    if smart is None:
        smart = 0

    # --------------------------------------------------------
    # PATTERN
    # --------------------------------------------------------

    pattern = safe_call(
        detect_pattern,
        pair,
        default=0,
        name="pattern_detector",
    )

    if pattern is None:
        pattern = 0

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    raw_score = safe_call(
        score_pair,
        pair,
        default=None,
        name="scorer",
    )

    score = extract_score(
        raw_score
    )

    if score is None:

        return None

    # A low base score can still be monitored,
    # but it won't be treated as a trade candidate.
    if score < MIN_SCORE:

        return None

    # --------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------

    simulation = safe_call(
        simulate,
        pair,
        default=None,
        name="simulator",
    )

    if simulation is None:

        return None

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    decision = safe_call(
        decide,
        score,
        risk,
        simulation,
        smart,
        pattern,
        default=None,
        name="decision_engine",
    )

    if not isinstance(
        decision,
        dict,
    ):

        return None

    return {
        "symbol": profile.get(
            "symbol",
            symbol,
        ),
        "address": profile.get(
            "address",
            address,
        ),
        "score": score,
        "smart_money": smart,
        "pattern": pattern,
        "simulation": simulation,
        "decision": decision,
        "timestamp": time.time(),
    }


# ============================================================
# LEARNING
# ============================================================

def learn(
    result: Dict[str, Any],
) -> None:

    try:

        save_prediction(
            result["symbol"],
            result["address"],
            result["score"],
        )

    except Exception as error:

        logger.error(
            "LEARNING ERROR: %s",
            error,
        )


# ============================================================
# EXECUTION HOOK
# ============================================================

def execute_trade(
    result: Dict[str, Any],
) -> bool:

    """
    This is intentionally an execution hook.

    Do NOT put a fake swap here.

    Connect this function to trade_manager.py once
    live execution has been tested independently.
    """

    decision = result.get(
        "decision",
        {},
    )

    if not decision.get(
        "trade",
        False,
    ):

        return False

    if RUN_MODE != "live":

        logger.info(
            "PAPER TRADE: %s | %s",
            result["symbol"],
            decision,
        )

        print(
            f"[PAPER] "
            f"{result['symbol']} | "
            f"{decision.get('level')} | "
            f"score={decision.get('score')}"
        )

        return False

    # Live mode intentionally does not execute automatically
    # until trade_manager.py is connected.
    logger.warning(
        "LIVE opportunity detected but "
        "execution manager is not connected: %s",
        result["symbol"],
    )

    return False


# ============================================================
# ONE CYCLE
# ============================================================

def run_cycle(
    state: Dict[str, Any],
) -> None:

    if not network_ok():

        logger.warning(
            "Network/API unavailable. "
            "Skipping cycle."
        )

        print(
            "[NETWORK] unavailable"
        )

        return

    # --------------------------------------------------------
    # SCAN
    # --------------------------------------------------------

    pairs = fetch_pairs()

    if not isinstance(
        pairs,
        list,
    ):

        raise ValueError(
            "fetch_pairs() "
            "must return list"
        )

    if not pairs:

        print(
            "[SCAN] no pairs"
        )

        return

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    pairs = filter_pairs(
        pairs
    )

    if not isinstance(
        pairs,
        list,
    ):

        raise ValueError(
            "filter_pairs() "
            "must return list"
        )

    pairs = pairs[
        :MAX_PAIRS_PER_CYCLE
    ]

    print(
        f"[SCAN] "
        f"{len(pairs)} candidates"
    )

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    results = []

    for pair in pairs:

        result = analyze_token(
            pair
        )

        if result is None:
            continue

        results.append(
            result
        )

        learn(
            result
        )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    results.sort(
        key=lambda item:
        get_number(
            item.get(
                "score",
                0,
            )
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        "\n"
        + "-" * 70
    )

    print(
        f"Qualified: "
        f"{len(results)}"
    )

    for item in results[
        :20
    ]:

        decision = item[
            "decision"
        ]

        print(
            f"{item['symbol']:15} "
            f"score={item['score']:6.2f} "
            f"level={decision.get('level')} "
            f"action={decision.get('action')}"
        )

    # --------------------------------------------------------
    # EXECUTION CANDIDATES
    # --------------------------------------------------------

    if trade_limit_reached(
        state
    ):

        print(
            "[LIMIT] "
            f"{MAX_DAILY_TRADES} daily "
            "trade limit reached."
        )

        return

    candidates = [
        item
        for item in results
        if item[
            "decision"
        ].get(
            "trade",
            False,
        )
    ]

    # Highest quality first.
    candidates.sort(
        key=lambda item:
        get_number(
            item[
                "decision"
            ].get(
                "score",
                item["score"],
            )
        ),
        reverse=True,
    )

    # --------------------------------------------------------
    # EXECUTE
    # --------------------------------------------------------

    for result in candidates:

        if trade_limit_reached(
            state
        ):

            break

        executed = execute_trade(
            result
        )

        if executed:

            state[
                "daily_trades"
            ] += 1

            save_state(
                state
            )

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    state[
        "last_scan"
    ] = time.time()

    state[
        "last_successful_scan"
    ] = time.time()

    state[
        "scan_count"
    ] += 1

    save_state(
        state
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        "👻 GHOST ENGINE"
    )

    print(
        "Continuous scanner"
    )

    print(
        f"Mode: {RUN_MODE}"
    )

    print(
        f"Interval: {SCAN_INTERVAL}s"
    )

    print(
        f"Daily max trades: "
        f"{MAX_DAILY_TRADES}"
    )

    print(
        f"Pairs/cycle: "
        f"{MAX_PAIRS_PER_CYCLE}"
    )

    # --------------------------------------------------------
    # LEARNING DB
    # --------------------------------------------------------

    try:

        create_learning_table()

    except Exception as error:

        logger.exception(
            "Learning DB initialization failed"
        )

        print(
            "[ERROR] learning database"
        )

        return

    # --------------------------------------------------------
    # LOOP
    # --------------------------------------------------------

    while True:

        started = time.time()

        state = load_state()

        print(
            "\n"
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Scanning | "
            f"daily trades="
            f"{state['daily_trades']}/"
            f"{MAX_DAILY_TRADES}"
        )

        try:

            run_cycle(
                state
            )

        except KeyboardInterrupt:

            print(
                "\nStopped."
            )

            break

        except Exception as error:

            logger.exception(
                "MAIN LOOP ERROR: %s",
                error,
            )

            state[
                "errors"
            ] += 1

            state[
                "last_error"
            ] = str(
                error
            )

            save_state(
                state
            )

            print(
                "[ERROR] "
                "cycle failed; retrying."
            )

            time.sleep(
                ERROR_RETRY_INTERVAL
            )

            continue

        # ----------------------------------------------------
        # MAINTAIN 3-SECOND CYCLE
        # ----------------------------------------------------

        elapsed = (
            time.time()
            - started
        )

        sleep_for = max(
            0.5,
            SCAN_INTERVAL
            - elapsed,
        )

        time.sleep(
            sleep_for
        )


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":

    main()
