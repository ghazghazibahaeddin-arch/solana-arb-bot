"""
Ghost Engine - Safe Mode

Central safety state.

Safe mode blocks trading decisions whenever
critical system conditions are unsafe.
"""

import json
import os
import threading
import time


STATE_FILE = "state.json"

_lock = threading.Lock()


def _default_state():

    return {
        "safe_mode": True,
        "reason": "startup",
        "timestamp": time.time(),
        "last_error": None,
        "last_recovery": None,
    }


def _load_state():

    if not os.path.exists(
        STATE_FILE
    ):

        return _default_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(
            data,
            dict
        ):

            return _default_state()

        return data

    except (
        OSError,
        json.JSONDecodeError
    ):

        return _default_state()


def _save_state(
    data
):

    temporary = (
        STATE_FILE
        +
        ".tmp"
    )

    with open(
        temporary,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2
        )

        file.flush()
        os.fsync(
            file.fileno()
        )

    os.replace(
        temporary,
        STATE_FILE
    )


def enter_safe_mode(
    reason: str,
    error=None
):

    with _lock:

        state = _load_state()

        state["safe_mode"] = True

        state["reason"] = str(
            reason
        )

        state["timestamp"] = time.time()

        state["last_error"] = (
            str(error)
            if error is not None
            else None
        )

        _save_state(
            state
        )

    print(
        f"[SAFE MODE] {reason}"
    )


def exit_safe_mode(
    reason="system_recovered"
):

    with _lock:

        state = _load_state()

        state["safe_mode"] = False

        state["reason"] = str(
            reason
        )

        state["timestamp"] = time.time()

        state["last_recovery"] = time.time()

        _save_state(
            state
        )

    print(
        f"[NORMAL MODE] {reason}"
    )


def is_safe_mode():

    with _lock:

        state = _load_state()

        return bool(
            state.get(
                "safe_mode",
                True
            )
        )


def get_state():

    with _lock:

        return _load_state()


def require_live_mode():

    """
    Returns True only when the system is explicitly
    out of safe mode.

    The caller must still perform its own risk checks.
    """

    return not is_safe_mode()
