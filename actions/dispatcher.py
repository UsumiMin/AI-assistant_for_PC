from collections.abc import Callable


class Dispatcher:
    def __init__(self) -> None:
        self._registry: dict[str, Callable[[], None]] = {}

    def register(self, command: str, action: Callable[[], None]) -> None:
        self._registry[command] = action

    def unregister(self, command: str) -> None:
        if command not in self._registry:
            error_msg = f'Unregistered Command - {command}'
            raise ValueError(error_msg)
        self._registry.pop(command)

    def dispatch(self, command: str) -> None:
        if command not in self._registry:
            error_msg = f'Unregistered Command - {command}'
            raise ValueError(error_msg)
        self._registry[command]()
