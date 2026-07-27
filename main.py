"""
Ghost Engine - Main Orchestrator

Pipeline:

Live Data
   ↓
Network Guard
   ↓
Scanner
   ↓
Filters
   ↓
Risk Engine
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
Learning Database

IMPORTANT:
This file does NOT force trades.
If data is missing, stale, inconsistent, or unsafe:
NO TRADE.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# OPTIONAL / REQUIRED MODULES
# ============================================================

from scanner import fetch_pairs
from filters import filter_pairs
from risk_engine import check
from data_fusion_engine import build_token_profile
from scorer import score_pair
from simulator import simulate
from smart_wallet_tracker import analyze as smart_money
from pattern_detector import detect_pattern
from decision_engine import decide

from learning_engine import (
    create_learning_table,
    save_prediction,
)


# ============================================================
# SAFETY MODULES
# ============================================================

try:
    from network_guard import check_all
except ImportError:
    check_all = None


try:
    from safe_mode import (
        enter_safe_mode,
        exit_safe_mode,
        is_safe_mode,
    )
except ImportError:

    def enter_safe_mode(reason, error=None):
        logging.warning(
            "SAFE MODE: %s | %s",
            reason,
            error,
        )

    def exit_safe_mode(reason="recovered"):
        logging.info(
            "NORMAL MODE: %s",
            reason,
        )

    def is_safe_mode():
        return False


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
        "100",
    )
)

MAX_RESULTS_PRINTED = int(
    os.getenv(
        "MAX_RESULTS_PRINTED",
        "10",
    )
)

# Safety default.
# Do not enable live execution from this file.
RUN_MODE = os.getenv(
    "RUN_MODE",
    "paper",
).lower()

MIN_SCORE = float(
    os.getenv(
        "MIN_SCORE",
        "70",
    )
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename="ghost_engine.log",
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

STATE_FILE = "state.json"


def load_state() -> Dict[str, Any]:

    default_state = {
        "safe_mode": True,
        "reason": "startup",
        "last_scan": 0,
        "last_successful_scan": 0,
        "last_heartbeat": 0,
        "scan_count": 0,
        "errors": 0,
        "last_error": None,
    }

    if not os.path.exists(
        STATE_FILE
    ):
        return default_state

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict,
        ):
            return default_state

        default_state.update(
            data
        )

        return default_state

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:

        logger.error(
            "STATE LOAD ERROR: %s",
            error,
        )

        return default_state


def save_state(
    updates: Dict[str, Any],
) -> None:

    state = load_state()

    state.update(
        updates
    )

    temporary_file = (
        STATE_FILE
        + ".tmp"
    )

    try:

        with open(
            temporary_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                state,
                file,
                indent=2,
            )

            file.flush()
            os.fsync(
                file.fileno()
            )

        os.replace(
            temporary_file,
            STATE_FILE,
        )

    except OSError as error:

        logger.error(
            "STATE SAVE ERROR: %s",
            error,
        )


# ============================================================
# HEARTBEAT
# ============================================================

def heartbeat() -> None:

    save_state(
        {
            "last_heartbeat": time.time(),
        }
    )


# ============================================================
# DATA VALIDATION
# ============================================================

def valid_pair(
    pair: Any,
) -> bool:

    if not isinstance(
        pair,
        dict,
    ):
        return False

    base_token = pair.get(
        "baseToken"
    )

    if not isinstance(
        base_token,
        dict,
    ):
        return False

    address = base_token.get(
        "address"
    )

    symbol = base_token.get(
        "symbol"
    )

    if not address:
        return False

    if not symbol:
        return False

    return True


def normalize_number(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        if value is None:
            return default

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# NETWORK HEALTH
# ============================================================

def network_is_healthy() -> bool:

    if check_all is None:

        logger.warning(
            "network_guard.py not available"
        )

        # We do not blindly trade without the guard.
        return False

    try:

        health = check_all()

        if not isinstance(
            health,
            dict,
        ):
            return False

        return bool(
            health.get(
                "healthy",
                False,
            )
        )

    except Exception as error:

        logger.error(
            "NETWORK CHECK ERROR: %s",
            error,
        )

        return False


# ============================================================
# SAFE MODULE CALL
# ============================================================

def call_module(
    func,
    *args,
    default=None,
    module_name="module",
):

    try:

        return func(
            *args
        )

    except Exception as error:

        logger.exception(
            "%s ERROR: %s",
            module_name,
            error,
        )

        return default


# ============================================================
# SCORE EXTRACTION
# ============================================================

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

                try:

                    return float(
                        value[key]
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

    return None


# ============================================================
# DECISION EXTRACTION
# ============================================================

def decision_is_tradeable(
    decision: Any,
) -> bool:

    if decision is None:
        return False

    if isinstance(
        decision,
        bool,
    ):
        return decision

    if isinstance(
        decision,
        dict,
    ):

        value = decision.get(
            "approved",
            decision.get(
                "trade",
                False,
            ),
        )

        return bool(
            value
        )

    if isinstance(
        decision,
        str,
    ):

        normalized = (
            decision
            .strip()
            .lower()
        )

        return normalized in {
            "buy",
            "approved",
            "trade",
            "enter",
            "execute",
        }

    return False


# ============================================================
# TOKEN ANALYSIS
# ============================================================

def analyze_token(
    pair: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not valid_pair(
        pair
    ):

        return None

    symbol = (
        pair
        .get("baseToken", {})
        .get("symbol", "UNKNOWN")
    )

    address = (
        pair
        .get("baseToken", {})
        .get("address")
    )

    # --------------------------------------------------------
    # 1. BASIC RISK
    # --------------------------------------------------------

    try:

        risk_result = check(
            pair
        )

        if not risk_result:

            logger.info(
                "REJECTED BY RISK: %s",
                symbol,
            )

            return None

    except Exception as error:

        logger.error(
            "RISK ERROR %s: %s",
            symbol,
            error,
        )

        return None

    # --------------------------------------------------------
    # 2. DATA FUSION
    # --------------------------------------------------------

    profile = call_module(
        build_token_profile,
        pair,
        default=None,
        module_name="data_fusion",
    )

    if not isinstance(
        profile,
        dict,
    ):

        return None

    # --------------------------------------------------------
    # 3. SMART MONEY
    # --------------------------------------------------------

    smart = call_module(
        smart_money,
        pair,
        default=0,
        module_name="smart_money",
    )

    if smart is None:
        smart = 0

    # --------------------------------------------------------
    # 4. PATTERN
    # --------------------------------------------------------

    pattern = call_module(
        detect_pattern,
        pair,
        default=0,
        module_name="pattern_detector",
    )

    if pattern is None:
        pattern = 0

    # --------------------------------------------------------
    # 5. SCORING
    # --------------------------------------------------------

    raw_score = call_module(
        score_pair,
        pair,
        default=None,
        module_name="scorer",
    )

    score = extract_score(
        raw_score
    )

    if score is None:

        logger.warning(
            "INVALID SCORE: %s",
            symbol,
        )

        return None

    # --------------------------------------------------------
    # 6. SCORE GATE
    # --------------------------------------------------------

    if score < MIN_SCORE:

        logger.info(
            "LOW SCORE: %s = %.2f",
            symbol,
            score,
        )

        return None

    # --------------------------------------------------------
    # 7. SIMULATION
    # --------------------------------------------------------

    simulation = call_module(
        simulate,
        pair,
        default=None,
        module_name="simulator",
    )

    if simulation is None:

        return None

    # --------------------------------------------------------
    # 8. DECISION
    # --------------------------------------------------------

    try:

        decision = decide(
            score,
            risk_result,
            simulation,
            smart,
            pattern,
        )

    except Exception as error:

        logger.error(
            "DECISION ERROR %s: %s",
            symbol,
            error,
        )

        return None

    # --------------------------------------------------------
    # 9. FINAL RESULT
    # --------------------------------------------------------

    result = {
        "symbol": (
            profile.get(
                "symbol",
                symbol,
            )
        ),
        "address": (
            profile.get(
                "address",
                address,
            )
        ),
        "score": score,
        "smart_money": smart,
        "pattern": pattern,
        "simulation": simulation,
        "decision": decision,
        "tradeable": decision_is_tradeable(
            decision
        ),
        "timestamp": time.time(),
    }

    return result


# ============================================================
# SAVE LEARNING DATA
# ============================================================

def save_learning_result(
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
            "LEARNING SAVE ERROR: %s",
            error,
        )


# ============================================================
# PRINT OPPORTUNITIES
# ============================================================

def print_opportunities(
    opportunities: List[
        Dict[str, Any]
    ],
) -> None:

    print(
        "\n"
        + "=" * 70
    )

    print(
        f"Qualified candidates: "
        f"{len(opportunities)}"
    )

    print(
        "=" * 70
    )

    for item in opportunities[
        :MAX_RESULTS_PRINTED
    ]:

        print(
            "\nTOKEN:",
            item["symbol"],
        )

        print(
            "ADDRESS:",
            item["address"],
        )

        print(
            "SCORE:",
            round(
                item["score"],
                2,
            ),
        )

        print(
            "SMART MONEY:",
            item["smart_money"],
        )

        print(
            "PATTERN:",
            item["pattern"],
        )

        print(
            "SIMULATION:",
            item["simulation"],
        )

        print(
            "DECISION:",
            item["decision"],
        )

        print(
            "TRADEABLE:",
            item["tradeable"],
        )


# ============================================================
# ONE SCAN CYCLE
# ============================================================

def scan_cycle() -> bool:

    heartbeat()

    # --------------------------------------------------------
    # NETWORK
    # --------------------------------------------------------

    if not network_is_healthy():

        enter_safe_mode(
            "network_or_api_health_failure"
        )

        print(
            "[SAFE MODE] "
            "Network/API health failed."
        )

        return False

    # --------------------------------------------------------
    # SCANNER
    # --------------------------------------------------------

    pairs = fetch_pairs()

    if not isinstance(
        pairs,
        list,
    ):

        raise ValueError(
            "scanner.fetch_pairs() "
            "must return a list"
        )

    if not pairs:

        logger.info(
            "Scanner returned no pairs."
        )

        return True

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    filtered = filter_pairs(
        pairs
    )

    if not isinstance(
        filtered,
        list,
    ):

        raise ValueError(
            "filter_pairs() "
            "must return a list"
        )

    # Prevent accidental huge cycles.
    filtered = filtered[
        :MAX_PAIRS_PER_CYCLE
    ]

    opportunities = []

    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

    for pair in filtered:

        if not valid_pair(
            pair
        ):
            continue

        result = analyze_token(
            pair
        )

        if result is None:
            continue

        opportunities.append(
            result
        )

        save_learning_result(
            result
        )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    opportunities.sort(
        key=lambda item: normalize_number(
            item.get(
                "score",
                0,
            )
        ),
        reverse=True,
    )

    print_opportunities(
        opportunities
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    now = time.time()

    state = load_state()

    save_state(
        {
            "safe_mode": False,
            "reason": "healthy_scan",
            "last_scan": now,
            "last_successful_scan": now,
            "last_heartbeat": now,
            "scan_count": (
                int(
                    state.get(
                        "scan_count",
                        0,
                    )
                )
                + 1
            ),
            "last_error": None,
        }
    )

    exit_safe_mode(
        "healthy_scan"
    )

    return True


# ============================================================
# MAIN LOOP
# ============================================================

def main():

    print(
        "\n"
        "👻 GHOST ENGINE"
    )

    print(
        "Starting..."
    )

    print(
        f"Mode: {RUN_MODE.upper()}"
    )

    print(
        f"Scan interval: "
        f"{SCAN_INTERVAL}s"
    )

    print(
        f"Minimum score: "
        f"{MIN_SCORE}"
    )

    print(
        "Safety: ENABLED"
    )

    # --------------------------------------------------------
    # LEARNING DATABASE
    # --------------------------------------------------------

    try:

        create_learning_table()

    except Exception as error:

        logger.exception(
            "LEARNING DATABASE INIT ERROR"
        )

        enter_safe_mode(
            "learning_database_initialization_failed",
            error,
        )

        # Do not continue blindly.
        return

    # --------------------------------------------------------
    # START SAFE
    # --------------------------------------------------------

    enter_safe_mode(
        "startup_validation"
    )

    while True:

        started_at = time.time()

        try:

            print(
                "\n"
                f"[{datetime.now().isoformat()}]"
                " scanning..."
            )

            scan_cycle()

        except KeyboardInterrupt:

            print(
                "\nGhost Engine stopped."
            )

            enter_safe_mode(
                "manual_shutdown"
            )

            break

        except Exception as error:

            logger.exception(
                "MAIN LOOP ERROR: %s",
                error,
            )

            state = load_state()

            save_state(
                {
                    "safe_mode": True,
                    "reason": "main_loop_exception",
                    "errors": (
                        int(
                            state.get(
                                "errors",
                                0,
                            )
                        )
                        + 1
                    ),
                    "last_error": str(
                        error
                    ),
                    "last_heartbeat": time.time(),
                }
            )

            enter_safe_mode(
                "main_loop_exception",
                error,
            )

            print(
                "[SAFE MODE] "
                "Cycle failed. "
                "No trade."
            )

            time.sleep(
                ERROR_RETRY_INTERVAL
            )

            continue

        elapsed = (
            time.time()
            - started_at
        )

        sleep_time = max(
            0.5,
            SCAN_INTERVAL
            - elapsed,
        )

        time.sleep(
            sleep_time
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
