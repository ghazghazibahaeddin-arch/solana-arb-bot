"""
Ghost Engine - Project Diagnostic

Run:

    python project_diagnostic.py

Purpose:
    Check project structure, Python syntax, imports,
    configuration, database, and core modules.

This script NEVER executes a real trade.
"""

import ast
import importlib
import os
import py_compile
import sqlite3
import traceback


# ============================================================
# CONFIG
# ============================================================

ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.getenv(
    "GHOST_DB_PATH",
    "data/history.db"
)

REQUIRED_FILES = [

    "main.py",
    "scanner.py",
    "scorer.py",
    "filters.py",
    "risk_engine.py",
    "simulator.py",

    "database.py",
    "config.py",

    "helius_client.py",
    "birdeye_client.py",
    "dexscreener_client.py",
    "geckoterminal_client.py",
    "jupiter_client.py",

    "smart_wallet_tracker.py",
    "early_buyer_detector.py",
    "holder_distribution.py",
    "dev_wallet_tracker.py",

    "rug_detector.py",
    "pattern_detector.py",
    "market_memory.py",

    "data_fusion_engine.py",
    "learning_engine.py",

    "market_simulation_brain.py",
    "token_lifecycle_engine.py",

    "decision_engine.py",
]


# ============================================================
# RESULT TRACKING
# ============================================================

results = []

errors = []
warnings = []


def ok(name, message):

    print(
        f"[OK]   {name}: {message}"
    )

    results.append(
        ("OK", name, message)
    )


def warn(name, message):

    print(
        f"[WARN] {name}: {message}"
    )

    warnings.append(
        (name, message)
    )

    results.append(
        ("WARN", name, message)
    )


def fail(name, message):

    print(
        f"[FAIL] {name}: {message}"
    )

    errors.append(
        (name, message)
    )

    results.append(
        ("FAIL", name, message)
    )


# ============================================================
# FILE EXISTENCE
# ============================================================

def check_files():

    print()
    print("=" * 70)
    print("1. FILE STRUCTURE")
    print("=" * 70)

    for filename in REQUIRED_FILES:

        path = os.path.join(
            ROOT,
            filename
        )

        if os.path.isfile(path):

            ok(
                filename,
                "exists"
            )

        else:

            warn(
                filename,
                "missing"
            )


# ============================================================
# PYTHON SYNTAX
# ============================================================

def check_python_syntax():

    print()
    print("=" * 70)
    print("2. PYTHON SYNTAX")
    print("=" * 70)

    files = [
        f
        for f in os.listdir(ROOT)
        if f.endswith(".py")
    ]

    for filename in files:

        path = os.path.join(
            ROOT,
            filename
        )

        try:

            py_compile.compile(
                path,
                doraise=True
            )

            ok(
                filename,
                "syntax valid"
            )

        except Exception as error:

            fail(
                filename,
                str(error)
            )


# ============================================================
# AST ANALYSIS
# ============================================================

def check_empty_python_files():

    print()
    print("=" * 70)
    print("3. EMPTY / USELESS PYTHON FILES")
    print("=" * 70)

    files = [
        f
        for f in os.listdir(ROOT)
        if f.endswith(".py")
    ]

    for filename in files:

        path = os.path.join(
            ROOT,
            filename
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                source = file.read()

            if not source.strip():

                warn(
                    filename,
                    "file is empty"
                )

                continue

            tree = ast.parse(
                source
            )

            meaningful_nodes = [
                node
                for node in tree.body
                if not isinstance(
                    node,
                    ast.Expr
                )
                or not (
                    isinstance(
                        node.value,
                        ast.Constant
                    )
                    and
                    isinstance(
                        node.value.value,
                        str
                    )
                )
            ]

            if not meaningful_nodes:

                warn(
                    filename,
                    "contains no executable code"
                )

            else:

                ok(
                    filename,
                    "contains executable code"
                )

        except Exception as error:

            fail(
                filename,
                str(error)
            )


# ============================================================
# IMPORT TEST
# ============================================================

def check_imports():

    print()
    print("=" * 70)
    print("4. MODULE IMPORTS")
    print("=" * 70)

    files = [
        f[:-3]
        for f in os.listdir(ROOT)
        if f.endswith(".py")
        and f != "__init__.py"
    ]

    for module_name in files:

        try:

            importlib.import_module(
                module_name
            )

            ok(
                module_name,
                "import successful"
            )

        except Exception as error:

            fail(
                module_name,
                (
                    f"{type(error).__name__}: "
                    f"{error}"
                )
            )


# ============================================================
# ENVIRONMENT
# ============================================================

def check_environment():

    print()
    print("=" * 70)
    print("5. ENVIRONMENT")
    print("=" * 70)

    env_path = os.path.join(
        ROOT,
        ".env"
    )

    if not os.path.isfile(
        env_path
    ):

        warn(
            ".env",
            "file not found"
        )

        return

    ok(
        ".env",
        "file exists"
    )

    try:

        from dotenv import load_dotenv

        load_dotenv(
            env_path
        )

    except ImportError:

        warn(
            ".env",
            "python-dotenv is not installed"
        )

        return

    keys = [

        "HELIUS_API_KEY",

        "BIRDEYE_API_KEY",

        "GEMINI_API_KEY",

        "GROQ_API_KEY",

    ]

    for key in keys:

        value = os.getenv(
            key
        )

        if value:

            ok(
                key,
                "configured"
            )

        else:

            warn(
                key,
                "missing"
            )


# ============================================================
# DATABASE
# ============================================================

def check_database():

    print()
    print("=" * 70)
    print("6. DATABASE")
    print("=" * 70)

    if not os.path.exists(
        DB_PATH
    ):

        warn(
            "database",
            f"{DB_PATH} does not exist yet"
        )

        return

    try:

        conn = sqlite3.connect(
            DB_PATH,
            timeout=10
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        )

        tables = {
            row[0]
            for row in cursor.fetchall()
        }

        conn.close()

        ok(
            "database",
            "SQLite connection successful"
        )

        print(
            "      Tables:",
            ", ".join(
                sorted(tables)
            )
            if tables
            else "none"
        )

        if "tokens" in tables:

            ok(
                "tokens table",
                "exists"
            )

        else:

            warn(
                "tokens table",
                "missing"
            )

    except Exception as error:

        fail(
            "database",
            str(error)
        )


# ============================================================
# CORE FUNCTION CHECK
# ============================================================

def check_functions():

    print()
    print("=" * 70)
    print("7. CORE FUNCTIONS")
    print("=" * 70)

    expected = {

        "scanner": [
            "fetch_pairs"
        ],

        "scorer": [
            "score_pair"
        ],

        "filters": [
            "filter_pairs"
        ],

        "risk_engine": [
            "check"
        ],

        "simulator": [
            "simulate"
        ],

        "smart_money": [
            "analyze"
        ],

        "pattern_detector": [
            "analyze"
        ],

        "market_simulation_brain": [
            "analyze_strategy"
        ],

        "token_lifecycle_engine": [
            "analyze_token"
        ],

    }

    for module_name, functions in expected.items():

        try:

            module = importlib.import_module(
                module_name
            )

        except Exception as error:

            fail(
                module_name,
                f"cannot import: {error}"
            )

            continue

        for function_name in functions:

            if hasattr(
                module,
                function_name
            ):

                ok(
                    f"{module_name}.{function_name}",
                    "exists"
                )

            else:

                fail(
                    f"{module_name}.{function_name}",
                    "function missing"
                )


# ============================================================
# DEPENDENCIES
# ============================================================

def check_dependencies():

    print()
    print("=" * 70)
    print("8. DEPENDENCIES")
    print("=" * 70)

    packages = [

        "requests",

        "dotenv",

    ]

    for package in packages:

        try:

            importlib.import_module(
                package
            )

            ok(
                package,
                "installed"
            )

        except ImportError:

            fail(
                package,
                "not installed"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("GHOST ENGINE DIAGNOSTIC")
    print("=" * 70)

    check_files()

    check_python_syntax()

    check_empty_python_files()

    check_dependencies()

    check_environment()

    check_database()

    check_imports()

    check_functions()

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        "Errors:",
        len(errors)
    )

    print(
        "Warnings:",
        len(warnings)
    )

    if errors:

        print()
        print(
            "PROJECT STATUS: FAILED"
        )

        print()
        print(
            "Errors requiring attention:"
        )

        for name, message in errors:

            print(
                f" - {name}: {message}"
            )

        return 1

    if warnings:

        print()
        print(
            "PROJECT STATUS: NOT READY"
        )

        print(
            "No Python errors were found, "
            "but warnings remain."
        )

        return 2

    print()
    print(
        "PROJECT STATUS: BASIC CHECK PASSED"
    )

    print(
        "Syntax, imports, configuration, "
        "database and core functions passed."
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
