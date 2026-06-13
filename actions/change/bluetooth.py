"""
bluetooth_control.py
====================

Управление состоянием Bluetooth-радио в Windows через WinRT-API
``Windows.Devices.Radios``. Мягкое переключение радио, как тумблер в
«Параметрах» Windows. Права администратора не требуются.

Зависимости
-----------
    pip install winsdk      # WinRT-проекция для Python. Можно заменить на winrt.

API
---
    import bluetooth as bt

    bt.set_bluetooth(True)        # включить
    bt.set_bluetooth(False)       # выключить
    bt.enable_bluetooth()
    bt.disable_bluetooth()
    bt.toggle_bluetooth()         # переключить
    bt.get_bluetooth()            # True / False / None (адаптер не найден)

CLI
---
    python bluetooth_control.py status   # on | off | toggle | status
"""

from __future__ import annotations

import asyncio
import sys
import threading

__all__ = [
    'set_bluetooth',
    'get_bluetooth',
    'enable_bluetooth',
    'disable_bluetooth',
    'toggle_bluetooth',
    'BluetoothError',
]


class BluetoothError(RuntimeError):
    """Ошибка управления Bluetooth."""


# ---------------------------------------------------------------------------
# Импорт WinRT-проекции (winsdk или winrt)
# ---------------------------------------------------------------------------
try:
    from winsdk.windows.devices.radios import (  # type: ignore
        Radio,
        RadioState,
        RadioKind,
        RadioAccessStatus,
    )
except ImportError:
    try:
        from winrt.windows.devices.radios import (  # type: ignore
            Radio,
            RadioState,
            RadioKind,
            RadioAccessStatus,
        )
    except ImportError as exc:
        raise ImportError(
            'Не найдена WinRT-проекция. Установите пакет: pip install winsdk'
        ) from exc


# ---------------------------------------------------------------------------
# Внутренние асинхронные операции WinRT
# ---------------------------------------------------------------------------
async def _get_radios():
    access = await Radio.request_access_async()
    if access != RadioAccessStatus.ALLOWED:
        raise BluetoothError(f'Доступ к управлению радио не разрешён (статус: {access}).')
    radios = await Radio.get_radios_async()
    return [r for r in radios if r.kind == RadioKind.BLUETOOTH]


async def _set(enabled: bool) -> bool:
    target = RadioState.ON if enabled else RadioState.OFF
    radios = await _get_radios()
    if not radios:
        return False
    for radio in radios:
        await radio.set_state_async(target)
    return True


async def _get():
    radios = await _get_radios()
    if not radios:
        return None
    return any(r.state == RadioState.ON for r in radios)


async def _toggle() -> bool:
    current = await _get()
    if current is None:
        raise BluetoothError('Bluetooth-адаптер не найден.')
    return await _set(not current)


# ---------------------------------------------------------------------------
# Синхронный запуск корутины (безопасный в любом контексте)
# ---------------------------------------------------------------------------
def _run(coro):
    """
    Блокирующе выполняет корутину и возвращает результат.

    Если активного цикла событий нет (обычный синхронный код) — используется
    ``asyncio.run``. Если код вызван из уже работающего цикла, ``asyncio.run``
    применять нельзя, поэтому корутина выполняется в отдельном потоке с
    собственным циклом — так синхронный вызов не конфликтует с этим циклом.
    """
    result, error = None, None

    def _worker() -> None:
        nonlocal result, error
        try:
            result = asyncio.run(coro)
        except BaseException as exc:  # пробрасываем в вызывающий поток
            error = exc

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join()

    if error is not None:
        raise error
    return result


# ---------------------------------------------------------------------------
# Публичный синхронный API
# ---------------------------------------------------------------------------
def set_bluetooth(enabled: bool) -> bool:
    """
    Включает (``enabled=True``) или выключает (``enabled=False``) Bluetooth.
    Возвращает True при успехе, False — если адаптер не найден.
    """
    return _run(_set(enabled))


def get_bluetooth():
    """Состояние Bluetooth: True — включён, False — выключен, None — не найден."""
    return _run(_get())


def enable_bluetooth() -> bool:
    """Включить Bluetooth."""
    return _run(_set(True))


def disable_bluetooth() -> bool:
    """Выключить Bluetooth."""
    return _run(_set(False))


def toggle_bluetooth() -> bool:
    """Переключить Bluetooth в противоположное состояние."""
    return _run(_toggle())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description='Управление состоянием Bluetooth в Windows через WinRT.'
    )
    parser.add_argument(
        'action',
        choices=['on', 'off', 'toggle', 'status'],
        help='Действие: on | off | toggle | status',
    )
    args = parser.parse_args(argv)

    try:
        if args.action == 'status':
            state = get_bluetooth()
            if state is None:
                print('Bluetooth: адаптер не найден.')
                return 2
            print(f'Bluetooth: {"включён" if state else "выключен"}')
            return 0

        if args.action == 'toggle':
            ok = toggle_bluetooth()
            word = 'переключён'
        else:
            ok = set_bluetooth(args.action == 'on')
            word = 'включён' if args.action == 'on' else 'выключен'

        if ok:
            print(f'Готово. Bluetooth: {word}.')
            return 0
        print('Не удалось: Bluetooth-адаптер не найден.')
        return 1

    except BluetoothError as exc:
        print(f'Ошибка: {exc}')
        return 3
    except Exception as exc:
        print(f'Ошибка: {exc}')
        return 1


if __name__ == '__main__':
    sys.exit(_main())