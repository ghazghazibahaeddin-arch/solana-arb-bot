"""
Ghost Engine - Market Simulation Brain

Purpose:
    Backtest the Ghost Intelligence strategy on REAL historical
    observations collected by the system.

Important:
    This module NEVER sends a real transaction.
    It only simulates entries/exits and measures whether a strategy
    would have worked historically.

Core ideas:
    1. Walk-forward simulation
    2. No future-data leakage
    3. Fees + slippage
    4. Stop loss
    5. Take profit
    6. Maximum holding time
    7. Drawdown measurement
    8. Win rate
    9. Profit factor
    10. Expectancy
    11. Monte-Carlo stress test
"""

import os
import sqlite3
import random
import statistics
from dataclasses import dataclass
from typing import List, Dict, Optional


# ============================================================
# CONFIG
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

POSITION_SIZE_PCT = float(
    os.getenv(
        "SIM_POSITION_SIZE_PCT",
        "0.05"
    )
)

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


# ============================================================
# DATA MODEL
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
    entry_price: float
    exit_price: float
    return_pct: float
    pnl: float
    reason: str
    holding_periods: int


# ============================================================
# DATABASE
# ============================================================

def connect_db():

    return sqlite3.connect(
        DB_PATH
    )


def ensure_tables():

    os.makedirs(
        os.path.dirname(DB_PATH) or ".",
        exist_ok=True
    )

    conn = connect_db()

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS simulation_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            token TEXT,

            entry_price REAL,

            exit_price REAL,

            return_pct REAL,

            pnl REAL,

            reason TEXT,

            holding_periods INTEGER,

            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

def find_columns():

    conn = connect_db()

    cur = conn.cursor()

    try:

        cur.execute(
            "PRAGMA table_info(tokens)"
        )

        rows = cur.fetchall()

    except Exception:

        conn.close()

        return []

    conn.close()

    return [
        row[1]
        for row in rows
    ]


def load_history():

    """
    Tries to read historical observations from the existing
    tokens table.

    Required:
        price

    Optional:
        symbol
        address
        score
        timestamp
    """

    columns = find_columns()

    if "price" not in columns:

        return []

    token_column = (
        "address"
        if "address" in columns
        else "symbol"
        if "symbol" in columns
        else None
    )

    score_column = (
        "score"
        if "score" in columns
        else None
    )

    timestamp_column = (
        "timestamp"
        if "timestamp" in columns
        else None
    )

    selected = []

    selected.append(
        token_column
        if token_column
        else "''"
    )

    selected.append("price")

    selected.append(
        score_column
        if score_column
        else "0"
    )

    selected.append(
        timestamp_column
        if timestamp_column
        else "rowid"
    )

    query = f"""
        SELECT
            {selected[0]},
            {selected[1]},
            {selected[2]},
            {selected[3]}
        FROM tokens
        WHERE price > 0
        ORDER BY {selected[3]} ASC
    """

    conn = connect_db()

    cur = conn.cursor()

    try:

        cur.execute(query)

        rows = cur.fetchall()

    except Exception:

        conn.close()

        return []

    conn.close()

    points = []

    for row in rows:

        try:

            token = str(row[0])

            price = float(row[1])

            score = float(row[2] or 0)

            timestamp = float(row[3])

            points.append(
                MarketPoint(
                    token=token,
                    timestamp=timestamp,
                    price=price,
                    score=score
                )
            )

        except Exception:

            continue

    return points


# ============================================================
# GROUP HISTORY BY TOKEN
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
            key=lambda x: x.timestamp
        )

    return grouped


# ============================================================
# SIMULATED EXIT
# ============================================================

def simulate_exit(
    history: List[MarketPoint],
    entry_index: int
):

    entry = history[entry_index]

    entry_price = entry.price

    if entry_price <= 0:

        return None

    max_index = min(
        len(history) - 1,
        entry_index
        +
        MAX_HOLD_OBSERVATIONS
    )

    for i in range(
        entry_index + 1,
        max_index + 1
    ):

        current = history[i]

        change = (
            current.price
            /
            entry_price
            -
            1
        )

        if change <= -STOP_LOSS_PCT:

            return current, "STOP_LOSS", i - entry_index

        if change >= TAKE_PROFIT_PCT:

            return current, "TAKE_PROFIT", i - entry_index

    exit_point = history[max_index]

    return (
        exit_point,
        "TIME_EXIT",
        max_index - entry_index
    )


# ============================================================
# SINGLE TRADE
# ============================================================

def simulate_trade(
    history: List[MarketPoint],
    entry_index: int,
    capital: float
):

    entry = history[entry_index]

    if entry.score < MIN_SCORE:

        return None, capital

    result = simulate_exit(
        history,
        entry_index
    )

    if not result:

        return None, capital

    exit_point, reason, holding = result

    entry_price = entry.price
    exit_price = exit_point.price

    gross_return = (
        exit_price
        /
        entry_price
        -
        1
    )

    # Entry + exit friction.
    effective_return = (
        gross_return
        -
        FEE_RATE * 2
        -
        SLIPPAGE_RATE * 2
    )

    position_value = (
        capital
        *
        POSITION_SIZE_PCT
    )

    pnl = (
        position_value
        *
        effective_return
    )

    new_capital = capital + pnl

    trade = SimTrade(

        token=entry.token,

        entry_price=entry_price,

        exit_price=exit_price,

        return_pct=effective_return * 100,

        pnl=pnl,

        reason=reason,

        holding_periods=holding

    )

    return trade, new_capital


# ============================================================
# WALK-FORWARD BACKTEST
# ============================================================

def run_backtest(
    points: Optional[List[MarketPoint]] = None
):

    if points is None:

        points = load_history()

    if not points:

        return {
            "status": "NO_DATA",
            "message": (
                "Not enough historical observations."
            )
        }

    grouped = group_by_token(
        points
    )

    capital = INITIAL_CAPITAL

    starting_capital = capital

    trades = []

    for token, history in grouped.items():

        if len(history) < 2:

            continue

        # Important:
        # We only use information available at the
        # entry point. We never look into the future
        # to decide whether to enter.

        for i in range(
            len(history) - 1
        ):

            trade, capital = simulate_trade(
                history,
                i,
                capital
            )

            if trade:

                trades.append(
                    trade
                )

    return build_report(
        starting_capital,
        capital,
        trades
    )


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
            "trades": 0
        }

    wins = [
        t for t in trades
        if t.pnl > 0
    ]

    losses = [
        t for t in trades
        if t.pnl < 0
    ]

    total_profit = sum(
        t.pnl
        for t in wins
    )

    total_loss = abs(
        sum(
            t.pnl
            for t in losses
        )
    )

    win_rate = (
        len(wins)
        /
        len(trades)
        *
        100
    )

    profit_factor = (
        total_profit
        /
        total_loss
        if total_loss > 0
        else float("inf")
    )

    expectancy = (
        sum(
            t.return_pct
            for t in trades
        )
        /
        len(trades)
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

    return {

        "status": "OK",

        "starting_capital":
            round(
                starting_capital,
                4
            ),

        "final_capital":
            round(
                final_capital,
                4
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
            round(
                profit_factor,
                3
            )
            if profit_factor != float("inf")
            else "INF",

        "expectancy_pct":
            round(
                expectancy,
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

    maximum = 0

    for trade in trades:

        capital += trade.pnl

        if capital > peak:

            peak = capital

        if peak > 0:

            drawdown = (
                peak - capital
            ) / peak * 100

            maximum = max(
                maximum,
                drawdown
            )

    return maximum


# ============================================================
# MONTE CARLO STRESS TEST
# ============================================================

def monte_carlo(
    trades,
    simulations=1000
):

    if not trades:

        return {}

    returns = [
        t.return_pct / 100
        for t in trades
    ]

    final_results = []

    for _ in range(
        simulations
    ):

        capital = INITIAL_CAPITAL

        shuffled = returns.copy()

        random.shuffle(
            shuffled
        )

        for r in shuffled:

            position = (
                capital
                *
                POSITION_SIZE_PCT
            )

            capital += (
                position * r
            )

        final_results.append(
            capital
        )

    final_results.sort()

    return {

        "simulations":
            simulations,

        "worst":
            round(
                final_results[0],
                4
            ),

        "p05":
            round(
                percentile(
                    final_results,
                    5
                ),
                4
            ),

        "median":
            round(
                statistics.median(
                    final_results
                ),
                4
            ),

        "p95":
            round(
                percentile(
                    final_results,
                    95
                ),
                4
            ),

        "best":
            round(
                final_results[-1],
                4
            )
    }


def percentile(
    values,
    p
):

    if not values:

        return 0

    index = (
        len(values) - 1
    ) * p / 100

    lower = int(index)

    upper = min(
        lower + 1,
        len(values) - 1
    )

    fraction = index - lower

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
# SAVE RESULTS
# ============================================================

def save_trades(
    trades
):

    ensure_tables()

    conn = connect_db()

    cur = conn.cursor()

    for trade in trades:

        cur.execute(
            """
            INSERT INTO simulation_results
            (
                token,
                entry_price,
                exit_price,
                return_pct,
                pnl,
                reason,
                holding_periods
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.token,
                trade.entry_price,
                trade.exit_price,
                trade.return_pct,
                trade.pnl,
                trade.reason,
                trade.holding_periods
            )
        )

    conn.commit()
    conn.close()


# ============================================================
# STRATEGY QUALITY CHECK
# ============================================================

def strategy_is_credible(
    report,
    monte_carlo_report
):

    if report.get("status") != "OK":

        return False

    if report["trades"] < 50:

        return False

    if report["expectancy_pct"] <= 0:

        return False

    if report["profit_factor"] != "INF":

        if report["profit_factor"] < 1.20:

            return False

    if report["max_drawdown_pct"] > 40:

        return False

    if monte_carlo_report:

        if (
            monte_carlo_report["p05"]
            <
            INITIAL_CAPITAL * 0.50
        ):

            return False

    return True


# ============================================================
# FULL ANALYSIS
# ============================================================

def analyze_strategy():

    ensure_tables()

    points = load_history()

    report = run_backtest(
        points
    )

    trades = []

    if points:

        grouped = group_by_token(
            points
        )

        capital = INITIAL_CAPITAL

        for token, history in grouped.items():

            for i in range(
                len(history) - 1
            ):

                trade, capital = simulate_trade(
                    history,
                    i,
                    capital
                )

                if trade:

                    trades.append(
                        trade
                    )

    save_trades(
        trades
    )

    mc = monte_carlo(
        trades,
        simulations=1000
    )

    credible = strategy_is_credible(
        report,
        mc
    )

    return {

        "backtest":
            report,

        "monte_carlo":
            mc,

        "credible":
            credible,

        "message":
            (
                "Strategy passed the "
                "current historical tests."
                if credible
                else
                "Strategy needs more "
                "data or improvement."
            )
    }


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("GHOST MARKET SIMULATION BRAIN")
    print("=" * 60)

    result = analyze_strategy()

    print()

    print("BACKTEST")
    print("-" * 60)

    for key, value in result[
        "backtest"
    ].items():

        print(
            f"{key}: {value}"
        )

    print()

    print("MONTE CARLO")
    print("-" * 60)

    for key, value in result[
        "monte_carlo"
    ].items():

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
