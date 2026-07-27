"""
Ghost Engine - Token Lifecycle Engine

Purpose
-------
Build a real-time lifecycle profile for newly discovered Solana tokens.

The engine observes a token from its first recorded snapshot and
tracks how its behavior changes over time.

It DOES NOT claim to know the future.

Instead it answers:

    "Does the current token resemble historical tokens
     that previously entered a strong expansion phase?"

Lifecycle:

    BIRTH
      ↓
    DISCOVERY
      ↓
    ACCUMULATION
      ↓
    EXPANSION
      ↓
    PARABOLIC
      ↓
    DISTRIBUTION
      ↓
    COLLAPSE

The engine uses only observations that actually exist in the database.
"""

import os
import math
import sqlite3
import statistics

from dataclasses import dataclass
from typing import List, Dict, Optional, Any


# ============================================================
# CONFIG
# ============================================================

DB_PATH = os.getenv(
    "GHOST_DB_PATH",
    "data/history.db"
)

# Minimum observations required before lifecycle classification.
MIN_OBSERVATIONS = int(
    os.getenv(
        "LIFECYCLE_MIN_OBSERVATIONS",
        "3"
    )
)

# Historical similarity threshold.
SIMILARITY_THRESHOLD = float(
    os.getenv(
        "LIFECYCLE_SIMILARITY_THRESHOLD",
        "0.75"
    )
)

# Maximum historical tokens used in comparison.
MAX_HISTORICAL_TOKENS = int(
    os.getenv(
        "LIFECYCLE_MAX_HISTORICAL_TOKENS",
        "1000"
    )
)


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class Snapshot:

    timestamp: float

    price: float
    liquidity: float
    volume: float

    buys: int
    sells: int

    holders: int
    score: float
    risk: float


@dataclass
class LifecycleState:

    phase: str

    age_seconds: float

    price_change_pct: float

    liquidity_change_pct: float

    volume_change_pct: float

    holder_change_pct: float

    buy_pressure: float

    momentum: float

    acceleration: float


# ============================================================
# DATABASE
# ============================================================

def connect():

    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True
    )

    return sqlite3.connect(
        DB_PATH,
        timeout=30
    )


def table_exists(
    table_name: str
):

    if not os.path.exists(DB_PATH):

        return False

    conn = connect()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = ?
            """,
            (table_name,)
        )

        return cursor.fetchone() is not None

    finally:

        conn.close()


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_float(value):

    try:

        if value is None:

            return 0.0

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return 0.0


def safe_int(value):

    try:

        if value is None:

            return 0

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        return 0


def percentage_change(
    old,
    new
):

    old = safe_float(old)
    new = safe_float(new)

    if old <= 0:

        return 0.0

    return (
        new / old - 1
    ) * 100


def clamp(
    value,
    minimum=0,
    maximum=100
):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


# ============================================================
# LOAD TOKEN HISTORY
# ============================================================

def load_token_history(
    address: str
) -> List[Snapshot]:
    """
    Load all real observations for one token.

    The earliest observation becomes the token's recorded
    birth point.

    Important:
        "Birth" here means first observation by Ghost,
        NOT necessarily the blockchain mint timestamp.
    """

    if not table_exists("tokens"):

        return []

    conn = connect()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                timestamp,
                price,
                liquidity,
                volume,
                buys,
                sells,
                holders,
                score,
                risk

            FROM tokens

            WHERE address = ?

            AND price > 0

            ORDER BY timestamp ASC
            """,
            (address,)
        )

        rows = cursor.fetchall()

    except sqlite3.Error:

        return []

    finally:

        conn.close()

    history = []

    for row in rows:

        try:

            history.append(
                Snapshot(

                    timestamp=safe_float(
                        row[0]
                    ),

                    price=safe_float(
                        row[1]
                    ),

                    liquidity=safe_float(
                        row[2]
                    ),

                    volume=safe_float(
                        row[3]
                    ),

                    buys=safe_int(
                        row[4]
                    ),

                    sells=safe_int(
                        row[5]
                    ),

                    holders=safe_int(
                        row[6]
                    ),

                    score=safe_float(
                        row[7]
                    ),

                    risk=safe_float(
                        row[8]
                    )
                )
            )

        except Exception:

            continue

    return history


# ============================================================
# MARKET FEATURES
# ============================================================

def buy_pressure(
    snapshot: Snapshot
):

    total = (
        snapshot.buys
        +
        snapshot.sells
    )

    if total <= 0:

        return 50.0

    return (
        snapshot.buys
        /
        total
    ) * 100


def calculate_momentum(
    previous: Snapshot,
    current: Snapshot
):

    if previous.price <= 0:

        return 0.0

    elapsed = (
        current.timestamp
        -
        previous.timestamp
    )

    if elapsed <= 0:

        return 0.0

    return (
        (
            current.price
            /
            previous.price
        )
        -
        1
    ) / elapsed


def calculate_acceleration(
    history: List[Snapshot]
):

    if len(history) < 3:

        return 0.0

    a = history[-3]
    b = history[-2]
    c = history[-1]

    first = calculate_momentum(
        a,
        b
    )

    second = calculate_momentum(
        b,
        c
    )

    if first == 0:

        return second

    return second - first


# ============================================================
# LIFECYCLE CLASSIFICATION
# ============================================================

def classify_phase(
    history: List[Snapshot]
):

    if not history:

        return "UNKNOWN"

    if len(history) < MIN_OBSERVATIONS:

        return "BIRTH"

    first = history[0]
    current = history[-1]

    price_change = percentage_change(
        first.price,
        current.price
    )

    liquidity_change = percentage_change(
        first.liquidity,
        current.liquidity
    )

    holder_change = percentage_change(
        first.holders,
        current.holders
    )

    pressure = buy_pressure(
        current
    )

    momentum = calculate_momentum(
        history[-2],
        current
    )

    acceleration = calculate_acceleration(
        history
    )

    # --------------------------------------------------------
    # COLLAPSE
    # --------------------------------------------------------

    if (
        price_change < -35
        and pressure < 40
    ):

        return "COLLAPSE"

    # --------------------------------------------------------
    # DISTRIBUTION
    # --------------------------------------------------------

    if (
        price_change > 30
        and pressure < 45
        and acceleration < 0
    ):

        return "DISTRIBUTION"

    # --------------------------------------------------------
    # PARABOLIC
    # --------------------------------------------------------

    if (
        price_change > 100
        and momentum > 0
        and acceleration > 0
    ):

        return "PARABOLIC"

    # --------------------------------------------------------
    # EXPANSION
    # --------------------------------------------------------

    if (
        price_change > 20
        and (
            liquidity_change > 10
            or
            holder_change > 10
        )
        and pressure >= 50
    ):

        return "EXPANSION"

    # --------------------------------------------------------
    # ACCUMULATION
    # --------------------------------------------------------

    if (
        abs(price_change) < 30
        and (
            liquidity_change > 0
            or
            holder_change > 0
        )
        and pressure >= 50
    ):

        return "ACCUMULATION"

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    return "DISCOVERY"


# ============================================================
# BUILD CURRENT STATE
# ============================================================

def build_state(
    history: List[Snapshot]
) -> Optional[LifecycleState]:

    if not history:

        return None

    first = history[0]
    current = history[-1]

    age = max(
        0,
        current.timestamp
        -
        first.timestamp
    )

    return LifecycleState(

        phase=classify_phase(
            history
        ),

        age_seconds=age,

        price_change_pct=percentage_change(
            first.price,
            current.price
        ),

        liquidity_change_pct=percentage_change(
            first.liquidity,
            current.liquidity
        ),

        volume_change_pct=percentage_change(
            first.volume,
            current.volume
        ),

        holder_change_pct=percentage_change(
            first.holders,
            current.holders
        ),

        buy_pressure=buy_pressure(
            current
        ),

        momentum=calculate_momentum(
            history[-2],
            current
        )
        if len(history) >= 2
        else 0.0,

        acceleration=calculate_acceleration(
            history
        )
    )


# ============================================================
# NORMALIZED TOKEN DNA
# ============================================================

def build_dna(
    history: List[Snapshot]
) -> Dict[str, float]:
    """
    Convert the current lifecycle into normalized features.

    These features are used for historical comparison.
    """

    state = build_state(
        history
    )

    if state is None:

        return {}

    return {

        "price_change":
            clamp(
                state.price_change_pct,
                -100,
                500
            ) / 500,

        "liquidity_change":
            clamp(
                state.liquidity_change_pct,
                -100,
                500
            ) / 500,

        "volume_change":
            clamp(
                state.volume_change_pct,
                -100,
                1000
            ) / 1000,

        "holder_change":
            clamp(
                state.holder_change_pct,
                -100,
                500
            ) / 500,

        "buy_pressure":
            state.buy_pressure / 100,

        "momentum":
            clamp(
                state.momentum * 100000,
                -100,
                100
            ) / 100,

        "acceleration":
            clamp(
                state.acceleration * 100000,
                -100,
                100
            ) / 100
    }


# ============================================================
# VECTOR DISTANCE
# ============================================================

def vector_similarity(
    first: Dict[str, float],
    second: Dict[str, float]
):

    keys = set(
        first.keys()
    ) & set(
        second.keys()
    )

    if not keys:

        return 0.0

    distances = []

    for key in keys:

        a = safe_float(
            first.get(key)
        )

        b = safe_float(
            second.get(key)
        )

        distance = abs(
            a - b
        )

        distances.append(
            distance
        )

    average_distance = statistics.mean(
        distances
    )

    similarity = (
        1
        -
        average_distance
    )

    return clamp(
        similarity * 100,
        0,
        100
    )


# ============================================================
# HISTORICAL TOKEN DISCOVERY
# ============================================================

def load_historical_addresses(
    exclude_address: Optional[str] = None
):

    if not table_exists("tokens"):

        return []

    conn = connect()

    try:

        cursor = conn.cursor()

        if exclude_address:

            cursor.execute(
                """
                SELECT
                    address

                FROM tokens

                WHERE address != ?

                GROUP BY address

                ORDER BY
                    MIN(timestamp) ASC

                LIMIT ?
                """,
                (
                    exclude_address,
                    MAX_HISTORICAL_TOKENS
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    address

                FROM tokens

                GROUP BY address

                ORDER BY
                    MIN(timestamp) ASC

                LIMIT ?
                """,
                (
                    MAX_HISTORICAL_TOKENS,
                )
            )

        return [
            row[0]
            for row in cursor.fetchall()
            if row[0]
        ]

    finally:

        conn.close()


# ============================================================
# HISTORICAL COMPARISON
# ============================================================

def compare_with_history(
    address: str
):

    current_history = load_token_history(
        address
    )

    if len(current_history) < MIN_OBSERVATIONS:

        return {
            "status": "INSUFFICIENT_DATA",
            "matches": []
        }

    current_dna = build_dna(
        current_history
    )

    historical_addresses = (
        load_historical_addresses(
            exclude_address=address
        )
    )

    matches = []

    for historical_address in historical_addresses:

        history = load_token_history(
            historical_address
        )

        if len(history) < MIN_OBSERVATIONS:

            continue

        historical_dna = build_dna(
            history
        )

        similarity = vector_similarity(
            current_dna,
            historical_dna
        )

        if similarity < (
            SIMILARITY_THRESHOLD * 100
        ):

            continue

        historical_state = build_state(
            history
        )

        if historical_state is None:

            continue

        matches.append({

            "address":
                historical_address,

            "similarity":
                round(
                    similarity,
                    2
                ),

            "phase":
                historical_state.phase,

            "historical_price_change_pct":
                round(
                    historical_state.price_change_pct,
                    2
                ),

            "historical_age_seconds":
                round(
                    historical_state.age_seconds,
                    2
                )
        })

    matches.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )

    return {

        "status": "OK",

        "matches":
            matches[:20]
    }


# ============================================================
# HISTORICAL OUTCOME ANALYSIS
# ============================================================

def analyze_historical_outcomes(
    matches: List[Dict[str, Any]]
):

    if not matches:

        return {

            "sample_size": 0,

            "average_change_pct": 0,

            "positive_rate_pct": 0,

            "strong_expansion_rate_pct": 0
        }

    changes = [
        safe_float(
            item.get(
                "historical_price_change_pct"
            )
        )
        for item in matches
    ]

    positive = [
        value
        for value in changes
        if value > 0
    ]

    strong = [
        value
        for value in changes
        if value >= 100
    ]

    return {

        "sample_size":
            len(changes),

        "average_change_pct":
            round(
                statistics.mean(
                    changes
                ),
                2
            ),

        "positive_rate_pct":
            round(
                len(positive)
                /
                len(changes)
                *
                100,
                2
            ),

        "strong_expansion_rate_pct":
            round(
                len(strong)
                /
                len(changes)
                *
                100,
                2
            )
    }


# ============================================================
# MAIN TOKEN ANALYSIS
# ============================================================

def analyze_token(
    address: str
):

    history = load_token_history(
        address
    )

    if not history:

        return {

            "status":
                "NOT_FOUND",

            "address":
                address
        }

    state = build_state(
        history
    )

    dna = build_dna(
        history
    )

    comparison = compare_with_history(
        address
    )

    outcomes = analyze_historical_outcomes(
        comparison.get(
            "matches",
            []
        )
    )

    return {

        "status":
            "OK",

        "address":
            address,

        "observations":
            len(history),

        "birth_timestamp":
            history[0].timestamp,

        "latest_timestamp":
            history[-1].timestamp,

        "phase":
            state.phase,

        "age_seconds":
            round(
                state.age_seconds,
                2
            ),

        "dna":
            dna,

        "current": {

            "price_change_pct":
                round(
                    state.price_change_pct,
                    2
                ),

            "liquidity_change_pct":
                round(
                    state.liquidity_change_pct,
                    2
                ),

            "volume_change_pct":
                round(
                    state.volume_change_pct,
                    2
                ),

            "holder_change_pct":
                round(
                    state.holder_change_pct,
                    2
                ),

            "buy_pressure":
                round(
                    state.buy_pressure,
                    2
                ),

            "momentum":
                state.momentum,

            "acceleration":
                state.acceleration
        },

        "historical_matches":
            comparison.get(
                "matches",
                []
            ),

        "historical_outcomes":
            outcomes
    }


# ============================================================
# DISCOVER EARLY TOKENS
# ============================================================

def discover_early_tokens(
    max_age_seconds: int = 3600
):

    """
    Find tokens that Ghost has observed recently.

    This does NOT claim they were created on-chain within
    this period. It means Ghost first observed them within
    this period.

    To determine actual blockchain creation time, combine
    this engine with Helius/Solana transaction data.
    """

    if not table_exists("tokens"):

        return []

    conn = connect()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                address,
                MIN(timestamp) AS first_seen

            FROM tokens

            GROUP BY address

            ORDER BY first_seen DESC
            """
        )

        rows = cursor.fetchall()

    finally:

        conn.close()

    import time

    now = time.time()

    result = []

    for address, first_seen in rows:

        age = (
            now
            -
            safe_float(first_seen)
        )

        if (
            age >= 0
            and
            age <= max_age_seconds
        ):

            result.append({

                "address":
                    address,

                "first_seen":
                    first_seen,

                "age_seconds":
                    round(
                        age,
                        2
                    )
            })

    return result


# ============================================================
# RANK EARLY OPPORTUNITIES
# ============================================================

def rank_early_tokens(
    max_age_seconds=3600
):

    candidates = discover_early_tokens(
        max_age_seconds
    )

    ranked = []

    for candidate in candidates:

        address = candidate[
            "address"
        ]

        analysis = analyze_token(
            address
        )

        if analysis.get(
            "status"
        ) != "OK":

            continue

        outcomes = analysis[
            "historical_outcomes"
        ]

        matches = analysis[
            "historical_matches"
        ]

        if not matches:

            similarity = 0

        else:

            similarity = max(
                item["similarity"]
                for item in matches
            )

        # This is NOT a probability of profit.
        #
        # It is merely a ranking score based on
        # historical resemblance + current behavior.

        ranking_score = (

            similarity * 0.50

            +

            outcomes[
                "positive_rate_pct"
            ] * 0.25

            +

            outcomes[
                "strong_expansion_rate_pct"
            ] * 0.25
        )

        ranked.append({

            "address":
                address,

            "phase":
                analysis[
                    "phase"
                ],

            "age_seconds":
                analysis[
                    "age_seconds"
                ],

            "similarity":
                round(
                    similarity,
                    2
                ),

            "historical_positive_rate":
                outcomes[
                    "positive_rate_pct"
                ],

            "historical_strong_expansion_rate":
                outcomes[
                    "strong_expansion_rate_pct"
                ],

            "ranking_score":
                round(
                    ranking_score,
                    2
                )
        })

    ranked.sort(
        key=lambda item:
            item["ranking_score"],
        reverse=True
    )

    return ranked


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "GHOST TOKEN LIFECYCLE ENGINE"
    )
    print("=" * 70)

    candidates = rank_early_tokens(
        max_age_seconds=3600
    )

    if not candidates:

        print(
            "No sufficiently observed "
            "early tokens found."
        )

    else:

        for index, token in enumerate(
            candidates[:20],
            start=1
        ):

            print()
            print(
                f"#{index}"
            )

            print(
                "Address:",
                token["address"]
            )

            print(
                "Age:",
                round(
                    token["age_seconds"],
                    1
                ),
                "seconds"
            )

            print(
                "Phase:",
                token["phase"]
            )

            print(
                "Historical similarity:",
                token["similarity"]
            )

            print(
                "Historical positive rate:",
                token[
                    "historical_positive_rate"
                ],
                "%"
            )

            print(
                "Historical strong expansion:",
                token[
                    "historical_strong_expansion_rate"
                ],
                "%"
            )

            print(
                "Ranking:",
                token["ranking_score"]
            )

    print()
