"""
Ghost Engine - Market Simulation Brain

Purpose
-------
Backtest the Ghost strategy against REAL historical snapshots
stored in data/history.db.

This module NEVER executes real trades.

Pipeline
--------
database.py
    ↓
REAL historical snapshots
    ↓
Market Simulation Brain
    ↓
Walk-forward backtest
    ↓
Risk / fee / slippage simulation
    ↓
Performance metrics
    ↓
Monte Carlo stress test

Important
---------
A profitable backtest is NOT a guarantee of future profit.
The engine refuses to call a strategy "credible" when there
is insufficient evidence.
"""

import os
import random
import sqlite3
import statistics

from dataclasses import dataclass
from typing import Optional, List, Dict


# ============================================================
# CONFIGURATION
# ============================================================

DB_PATH = os.getenv(
    "GHOST_DB_PATH",
    "data/history.db"
)

INITIAL_CAPITAL = float(
    os.getenv(
        "SIM_INITIAL_CAPITAL",
        "100"
    )
)

# Percentage of current capital risked per simulated trade.
POSITION_SIZE_PCT = float(
    os.getenv(
        "SIM_POSITION_SIZE_PCT",
        "0.05"
    )
)

# Approximate total trading friction.
FEE_RATE = float(
    os.getenv(
        "SIM_FEE_RATE",
        "0.003"
    )
)

SLIPPAGE_RATE = float(
    os.getenv(
        "SIM_SLIPPAGE_RATE",
        "0.005"
    )
)

STOP_LOSS_PCT = float(
    os.getenv(
        "SIM_STOP_LOSS_PCT",
        "0.12"
    )
)

TAKE_PROFIT_PCT = float(
    os.getenv(
        "SIM_TAKE_PROFIT_PCT",
        "0.30"
    )
)

MAX_HOLD_OBSERVATIONS = int(
    os.getenv(
        "SIM_MAX_HOLD_OBSERVATIONS",
        "20"
    )
)

MIN_SCORE = float(
    os.getenv(
        "SIM_MIN_SCORE",
        "85"
    )
)

MIN_TRADES_FOR_CREDIBILITY = int(
    os.getenv(
        "SIM_MIN_TRADES",
        "50"
    )
)

MAX_ACCEPTABLE_DRAWDOWN = float(
    os.getenv(
        "SIM_MAX_DRAWDOWN",
        "40"
    )
)

MONTE_CARLO_RUNS = int(
    os.getenv(
        "SIM_MONTE_CARLO_RUNS",
        "1000"
    )
)


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class MarketPoint:

    token: str
    timestamp: float
    price: float
    score: float
    risk: float = 0.0


@dataclass
class SimTrade:

    token: str

    entry_timestamp: float
    exit_timestamp: float

    entry_price: float
    exit_price: float

    gross_return_pct: float
    net_return_pct: float

    position_size: float
    pnl: float

    reason: str
    holding_periods: int


# ============================================================
# DATABASE
# ============================================================

def connect_db():

    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True
    )

    return sqlite3.connect(
        DB_PATH,
        timeout=30
    )


def ensure_simulation_table():

    conn = connect_db()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS simulation_results (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                token TEXT,

                entry_timestamp REAL,

                exit_timestamp REAL,

                entry_price REAL,

                exit_price REAL,

                gross_return_pct REAL,

                net_return_pct REAL,

                position_size REAL,

                pnl REAL,

                reason TEXT,

                holding_periods INTEGER,

                timestamp DATETIME
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# LOAD REAL HISTORICAL DATA
# ============================================================

def load_history() -> List[MarketPoint]:
    """
    Read real observations previously collected by scanner.py.

    Expected table:
        tokens

    Expected columns:
        address
        price
        score
        timestamp
    """

    if not os.path.exists(DB_PATH):

        return []

    conn = connect_db()

    try:

        cursor = conn.cursor()

        cursor.execute(
            "PRAGMA table_info(tokens)"
        )

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        required = {
            "address",
            "price",
            "timestamp"
        }

        if not required.issubset(columns):

            return []

        score_expression = (
            "score"
            if "score" in columns
            else "0"
        )

        risk_expression = (
            "risk"
            if "risk" in columns
            else "0"
        )

        cursor.execute(
            f"""
            SELECT
                address,
                price,
                {score_expression},
                {risk_expression},
                timestamp

            FROM tokens

            WHERE
                address IS NOT NULL
                AND address != ''
                AND price > 0
                AND timestamp IS NOT NULL

            ORDER BY
                address ASC,
                timestamp ASC
            """
        )

        rows = cursor.fetchall()

    except sqlite3.Error as error:

        print(
            f"[SIM] Database error: {error}"
        )

        return []

    finally:

        conn.close()

    points = []

    for row in rows:

        try:

            points.append(
                MarketPoint(

                    token=str(
                        row[0]
                    ),

                    price=float(
                        row[1]
                    ),

                    score=float(
                        row[2] or 0
                    ),

                    risk=float(
                        row[3] or 0
                    ),

                    timestamp=float(
                        row[4]
                    )
                )
            )

        except (
            TypeError,
            ValueError
        ):

            continue

    return points


# ============================================================
# GROUP BY TOKEN
# ============================================================

def group_by_token(
    points: List[MarketPoint]
):

    grouped = {}

    for point in points:

        grouped.setdefault(
            point.token,
            []
        ).append(point)

    for token in grouped:

        grouped[token].sort(
            key=lambda p: p.timestamp
        )

    return grouped


# ============================================================
# ENTRY FILTER
# ============================================================

def should_enter(
    point: MarketPoint
):
    """
    Entry decision uses ONLY information available
    at this exact observation.
    """

    if point.price <= 0:

        return False

    if point.score < MIN_SCORE:

        return False

    if point.risk > 50:

        return False

    return True


# ============================================================
# EXIT SIMULATION
# ============================================================

def simulate_exit(
    history: List[MarketPoint],
    entry_index: int
):
    """
    Simulate what would have happened AFTER entry.

    Future observations are used ONLY to determine
    the outcome of an already-entered simulated trade.
    """

    entry = history[
        entry_index
    ]

    entry_price = entry.price

    last_index = min(
        len(history) - 1,

        entry_index
        +
        MAX_HOLD_OBSERVATIONS
    )

    for index in range(
        entry_index + 1,
        last_index + 1
    ):

        point = history[index]

        change = (
            point.price
            /
            entry_price
            -
            1
        )

        if change <= -STOP_LOSS_PCT:

            return (
                point,
                "STOP_LOSS",
                index - entry_index
            )

        if change >= TAKE_PROFIT_PCT:

            return (
                point,
                "TAKE_PROFIT",
                index - entry_index
            )

    point = history[
        last_index
    ]

    return (
        point,
        "TIME_EXIT",
        last_index - entry_index
    )


# ============================================================
# SINGLE SIMULATED TRADE
# ============================================================

def simulate_trade(
    history: List[MarketPoint],
    entry_index: int,
    capital: float
):

    entry = history[
        entry_index
    ]

    if not should_enter(
        entry
    ):

        return None, capital

    if entry_index >= len(history) - 1:

        return None, capital

    result = simulate_exit(
        history,
        entry_index
    )

    if result is None:

        return None, capital

    exit_point, reason, holding = result

    entry_price = entry.price
    exit_price = exit_point.price

    if entry_price <= 0:

        return None, capital

    gross_return = (
        exit_price
        /
        entry_price
        -
        1
    )

    # Entry and exit friction.
    total_cost = (
        FEE_RATE * 2
        +
        SLIPPAGE_RATE * 2
    )

    net_return = (
        gross_return
        -
        total_cost
    )

    position_size = (
        capital
        *
        POSITION_SIZE_PCT
    )

    pnl = (
        position_size
        *
        net_return
    )

    new_capital = (
        capital
        +
        pnl
    )

    # Capital can never become negative in this simulator.
    new_capital = max(
        new_capital,
        0
    )

    trade = SimTrade(

        token=entry.token,

        entry_timestamp=entry.timestamp,

        exit_timestamp=exit_point.timestamp,

        entry_price=entry_price,

        exit_price=exit_price,

        gross_return_pct=(
            gross_return * 100
        ),

        net_return_pct=(
            net_return * 100
        ),

        position_size=position_size,

        pnl=pnl,

        reason=reason,

        holding_periods=holding
    )

    return trade, new_capital


# ============================================================
# WALK-FORWARD BACKTEST
# ============================================================

def run_backtest(
    points: Optional[
        List[MarketPoint]
    ] = None
):
    """
    Walk through historical data chronologically.

    No future observation is used to decide whether
    an entry signal existed.
    """

    if points is None:

        points = load_history()

    if not points:

        return {
            "status": "NO_DATA",
            "message": (
                "No historical snapshots "
                "were found in the database."
            ),
            "trades": []
        }

    grouped = group_by_token(
        points
    )

    capital = INITIAL_CAPITAL

    trades = []

    for token, history in grouped.items():

        if len(history) < 2:

            continue

        index = 0

        while index < len(history) - 1:

            trade, new_capital = simulate_trade(
                history,
                index,
                capital
            )

            if trade is None:

                index += 1

                continue

            trades.append(
                trade
            )

            capital = new_capital

            # Do not open another simulated position
            # while the previous one is still active.
            index += max(
                trade.holding_periods,
                1
            )

    report = build_report(
        INITIAL_CAPITAL,
        capital,
        trades
    )

    return {
        "status": report["status"],
        "report": report,
        "trades": trades
    }


# ============================================================
# PERFORMANCE REPORT
# ============================================================

def build_report(
    starting_capital,
    final_capital,
    trades
):

    if not trades:

        return {
            "status": "NO_TRADES",

            "starting_capital":
                starting_capital,

            "final_capital":
                final_capital,

            "return_pct":
                0,

            "trades":
                0
        }

    wins = [
        trade
        for trade in trades
        if trade.pnl > 0
    ]

    losses = [
        trade
        for trade in trades
        if trade.pnl < 0
    ]

    total_profit = sum(
        trade.pnl
        for trade in wins
    )

    total_loss = abs(
        sum(
            trade.pnl
            for trade in losses
        )
    )

    win_rate = (
        len(wins)
        /
        len(trades)
        *
        100
    )

    if total_loss > 0:

        profit_factor = (
            total_profit
            /
            total_loss
        )

    else:

        profit_factor = float(
            "inf"
        )

    expectancy = statistics.mean(
        trade.net_return_pct
        for trade in trades
    )

    return_pct = (
        final_capital
        /
        starting_capital
        -
        1
    ) * 100

    max_drawdown = calculate_drawdown(
        trades,
        starting_capital
    )

    average_win = (
        statistics.mean(
            trade.net_return_pct
            for trade in wins
        )
        if wins
        else 0
    )

    average_loss = (
        statistics.mean(
            trade.net_return_pct
            for trade in losses
        )
        if losses
        else 0
    )

    return {

        "status": "OK",

        "starting_capital":
            round(
                starting_capital,
                6
            ),

        "final_capital":
            round(
                final_capital,
                6
            ),

        "return_pct":
            round(
                return_pct,
                4
            ),

        "trades":
            len(trades),

        "wins":
            len(wins),

        "losses":
            len(losses),

        "win_rate":
            round(
                win_rate,
                2
            ),

        "profit_factor":
            (
                "INF"
                if profit_factor
                == float("inf")
                else round(
                    profit_factor,
                    4
                )
            ),

        "expectancy_pct":
            round(
                expectancy,
                4
            ),

        "average_win_pct":
            round(
                average_win,
                4
            ),

        "average_loss_pct":
            round(
                average_loss,
                4
            ),

        "max_drawdown_pct":
            round(
                max_drawdown,
                4
            )
    }


# ============================================================
# DRAWDOWN
# ============================================================

def calculate_drawdown(
    trades,
    starting_capital
):

    capital = starting_capital
    peak = capital
    maximum_drawdown = 0

    for trade in trades:

        capital += trade.pnl

        if capital > peak:

            peak = capital

        if peak <= 0:

            continue

        drawdown = (
            peak
            -
            capital
        ) / peak * 100

        maximum_drawdown = max(
            maximum_drawdown,
            drawdown
        )

    return maximum_drawdown


# ============================================================
# MONTE CARLO
# ============================================================

def monte_carlo(
    trades,
    simulations=MONTE_CARLO_RUNS
):
    """
    Randomizes the order of historical trade returns.

    This tests how sensitive the result is to trade ordering.
    """

    if not trades:

        return {
            "status": "NO_DATA"
        }

    returns = [
        trade.net_return_pct / 100
        for trade in trades
    ]

    final_capitals = []

    for _ in range(
        simulations
    ):

        shuffled = list(
            returns
        )

        random.shuffle(
            shuffled
        )

        capital = INITIAL_CAPITAL

        for trade_return in shuffled:

            position_size = (
                capital
                *
                POSITION_SIZE_PCT
            )

            pnl = (
                position_size
                *
                trade_return
            )

            capital += pnl

            capital = max(
                capital,
                0
            )

        final_capitals.append(
            capital
        )

    final_capitals.sort()

    return {

        "status": "OK",

        "simulations":
            simulations,

        "worst":
            round(
                final_capitals[0],
                6
            ),

        "p05":
            round(
                percentile(
                    final_capitals,
                    5
                ),
                6
            ),

        "median":
            round(
                statistics.median(
                    final_capitals
                ),
                6
            ),

        "p95":
            round(
                percentile(
                    final_capitals,
                    95
                ),
                6
            ),

        "best":
            round(
                final_capitals[-1],
                6
            )
    }


def percentile(
    values,
    percentage
):

    if not values:

        return 0

    index = (
        len(values) - 1
    ) * (
        percentage / 100
    )

    lower = int(index)

    upper = min(
        lower + 1,
        len(values) - 1
    )

    fraction = (
        index - lower
    )

    return (
        values[lower]
        +
        (
            values[upper]
            -
            values[lower]
        )
        *
        fraction
    )


# ============================================================
# SAVE SIMULATED TRADES
# ============================================================

def save_trades(
    trades
):

    if not trades:

        return

    ensure_simulation_table()

    conn = connect_db()

    try:

        for trade in trades:

            conn.execute(
                """
                INSERT INTO simulation_results (

                    token,
                    entry_timestamp,
                    exit_timestamp,
                    entry_price,
                    exit_price,
                    gross_return_pct,
                    net_return_pct,
                    position_size,
                    pnl,
                    reason,
                    holding_periods

                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    trade.token,

                    trade.entry_timestamp,

                    trade.exit_timestamp,

                    trade.entry_price,

                    trade.exit_price,

                    trade.gross_return_pct,

                    trade.net_return_pct,

                    trade.position_size,

                    trade.pnl,

                    trade.reason,

                    trade.holding_periods
                )
            )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# CREDIBILITY CHECK
# ============================================================

def strategy_is_credible(
    report,
    mc_report
):
    """
    Conservative gate.

    A strategy is NOT considered credible merely because
    the final capital increased.
    """

    if not report:

        return False

    if report.get(
        "status"
    ) != "OK":

        return False

    if report.get(
        "trades",
        0
    ) < MIN_TRADES_FOR_CREDIBILITY:

        return False

    if report.get(
        "expectancy_pct",
        0
    ) <= 0:

        return False

    profit_factor = report.get(
        "profit_factor"
    )

    if profit_factor != "INF":

        if profit_factor < 1.20:

            return False

    if report.get(
        "max_drawdown_pct",
        100
    ) > MAX_ACCEPTABLE_DRAWDOWN:

        return False

    if mc_report.get(
        "status"
    ) != "OK":

        return False

    # If the 5th percentile scenario loses
    # more than half the starting capital,
    # reject the strategy.
    if mc_report.get(
        "p05",
        0
    ) < INITIAL_CAPITAL * 0.50:

        return False

    return True


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def analyze_strategy():

    ensure_simulation_table()

    points = load_history()

    if not points:

        return {

            "status": "NO_DATA",

            "message": (
                "No real historical snapshots "
                "are available yet. "
                "Run scanner.py first."
            )
        }

    result = run_backtest(
        points
    )

    report = result.get(
        "report"
    )

    trades = result.get(
        "trades",
        []
    )

    if not trades:

        return {

            "status": "NO_TRADES",

            "message": (
                "Historical data exists, "
                "but the current strategy "
                "did not produce qualifying "
                "entries."
            )
        }

    save_trades(
        trades
    )

    mc = monte_carlo(
        trades
    )

    credible = strategy_is_credible(
        report,
        mc
    )

    return {

        "status": "OK",

        "backtest":
            report,

        "monte_carlo":
            mc,

        "credible":
            credible,

        "message": (
            "Strategy passed the current "
            "historical validation gates."
            if credible
            else
            "Strategy did NOT pass the "
            "current validation gates."
        )
    }


# ============================================================
# PRINT REPORT
# ============================================================

def print_report(
    result
):

    print()
    print("=" * 65)
    print(
        "GHOST MARKET SIMULATION BRAIN"
    )
    print("=" * 65)

    print()

    if result.get(
        "status"
    ) != "OK":

        print(
            result.get(
                "message",
                "No result."
            )
        )

        return

    report = result[
        "backtest"
    ]

    mc = result[
        "monte_carlo"
    ]

    print("BACKTEST")
    print("-" * 65)

    for key, value in report.items():

        print(
            f"{key}: {value}"
        )

    print()

    print("MONTE CARLO")
    print("-" * 65)

    for key, value in mc.items():

        print(
            f"{key}: {value}"
        )

    print()

    print(
        "STRATEGY CREDIBLE:",
        result["credible"]
    )

    print()

    print(
        result["message"]
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    result = analyze_strategy()

    print_report(
        result
)
