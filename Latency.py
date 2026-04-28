import sys
import threading


def print_with_timeout(text: str, timeout: float = 1.0) -> None:
    """
    Выводит текст в консоль с гарантией, что он появится
    не позднее чем через <timeout> секунд после вызова.
    """
    print(text, end="", flush=True)

    timer = threading.Timer(timeout, sys.stdout.flush)
    timer.daemon = True
    timer.start()
