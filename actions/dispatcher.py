from collections.abc import Callable
from typing import Any


class Dispatcher:
    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., None]] = {}

    def register(self, command: str, action: Callable[..., None]) -> None:
        self._registry[command] = action

    def unregister(self, command: str) -> None:
        self._check_command_registry(command)
        self._registry.pop(command)

    def dispatch(self, command: str, kwargs: dict[str, Any] | None = None) -> None:
        self._check_command_registry(command)
        if kwargs:
            self._registry[command](**kwargs)
        else:
            self._registry[command]()

    def _check_command_registry(self, command: str) -> None:
        """Raises ValueError if command not in registry"""
        if command not in self._registry:
            error_msg = f'Unregistered Command - {command}'
            raise ValueError(error_msg)
