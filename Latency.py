import sys
import threading


def print_with_timeout(text: str, timeout: float = 1.0) -> None:
    print(text, end="", flush=True)

    timer = threading.Timer(timeout, sys.stdout.flush)
    timer.daemon = True
    timer.start()
