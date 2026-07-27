"""
Ghost Engine - Watchdog

Runs main.py as a child process.

If main.py crashes, watchdog restarts it.

This module does NOT execute trades.
"""

import os
import signal
import subprocess
import sys
import time


RESTART_DELAY = float(
    os.getenv(
        "WATCHDOG_RESTART_DELAY",
        "5"
    )
)

MAX_RESTARTS = int(
    os.getenv(
        "WATCHDOG_MAX_RESTARTS",
        "20"
    )
)

WINDOW_SECONDS = int(
    os.getenv(
        "WATCHDOG_WINDOW_SECONDS",
        "300"
    )
)


def start_main():

    print(
        "[WATCHDOG] Starting main.py"
    )

    return subprocess.Popen(
        [
            sys.executable,
            "main.py"
        ],
        stdin=subprocess.DEVNULL
    )


def stop_process(
    process
):

    if process is None:

        return

    if process.poll() is not None:

        return

    try:

        process.terminate()

        process.wait(
            timeout=10
        )

    except subprocess.TimeoutExpired:

        process.kill()

        process.wait()


def run():

    process = None

    restart_times = []

    try:

        while True:

            now = time.time()

            restart_times = [
                timestamp
                for timestamp in restart_times
                if (
                    now - timestamp
                    <= WINDOW_SECONDS
                )
            ]

            if (
                len(restart_times)
                >= MAX_RESTARTS
            ):

                print(
                    "[WATCHDOG] Too many "
                    "restarts."
                )

                print(
                    "[WATCHDOG] Giving up "
                    "temporarily."
                )

                time.sleep(
                    60
                )

                restart_times.clear()

            if (
                process is None
                or
                process.poll() is not None
            ):

                if process is not None:

                    print(
                        "[WATCHDOG] main.py "
                        f"exited with code "
                        f"{process.returncode}"
                    )

                restart_times.append(
                    time.time()
                )

                process = start_main()

                time.sleep(
                    RESTART_DELAY
                )

            else:

                time.sleep(
                    2
                )

    except KeyboardInterrupt:

        print(
            "\n[WATCHDOG] Shutdown requested."
        )

    finally:

        stop_process(
            process
        )


if __name__ == "__main__":

    run()
