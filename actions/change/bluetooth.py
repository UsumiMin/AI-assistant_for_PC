"""
bluetooth_control.py
====================

Модуль для управления состоянием Bluetooth-радио в Windows через WinRT-API
``Windows.Devices.Radios``.

Это «мягкое» переключение радио — точно такое же, как тумблер Bluetooth в
«Параметрах» Windows / Центре уведомлений. Права администратора НЕ требуются.

Зависимости
-----------
    pip install winsdk      # WinRT-проекция для Python. Можно заменить на winrt.

Использование из командной строки
---------------------------------
    python bluetooth_control.py status
    python bluetooth_control.py on
    python bluetooth_control.py off
    python bluetooth_control.py toggle

Использование как модуля
------------------------
    import bluetooth_control as bt

    bt.set_bluetooth(True)        # включить
    bt.set_bluetooth(False)       # выключить
    bt.toggle_bluetooth()         # переключить
    print(bt.get_bluetooth())     # True / False / None (адаптер не найден)

Примечание: модуль предназначен для Windows.
"""

from __future__ import annotations

import asyncio
import sys

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
# Асинхронные операции WinRT
# ---------------------------------------------------------------------------
async def _get_bluetooth_radios():
    """Запрашивает доступ и возвращает список Bluetooth-радио."""
    access = await Radio.request_access_async()
    if access != RadioAccessStatus.ALLOWED:
        raise BluetoothError(f'Доступ к управлению радио не разрешён (статус: {access}).')
    radios = await Radio.get_radios_async()
    return [r for r in radios if r.kind == RadioKind.BLUETOOTH]


async def _set_async(turn_on: bool) -> bool:
    target = RadioState.ON if turn_on else RadioState.OFF
    radios = await _get_bluetooth_radios()
    if not radios:
        return False
    for radio in radios:
        await radio.set_state_async(target)
    return True


async def _get_async():
    radios = await _get_bluetooth_radios()
    if not radios:
        return None
    return any(r.state == RadioState.ON for r in radios)


def _run(coro):
    """Синхронно выполняет корутину WinRT."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Публичный интерфейс
# ---------------------------------------------------------------------------
def set_bluetooth(enabled: bool) -> bool:
    """
    Включает (``enabled=True``) или выключает (``enabled=False``) Bluetooth.
    Возвращает True при успехе, False — если Bluetooth-адаптер не найден.
    """
    return _run(_set_async(enabled))


def get_bluetooth():
    """
    Текущее состояние Bluetooth:
        True  — включён,
        False — выключен,
        None  — адаптер не найден.
    """
    return _run(_get_async())


def enable_bluetooth() -> bool:
    """Включить Bluetooth."""
    return set_bluetooth(True)


def disable_bluetooth() -> bool:
    """Выключить Bluetooth."""
    return set_bluetooth(False)


def toggle_bluetooth() -> bool:
    """Переключить Bluetooth в противоположное состояние."""
    current = get_bluetooth()
    if current is None:
        raise BluetoothError('Bluetooth-адаптер не найден.')
    return set_bluetooth(not current)


# ---------------------------------------------------------------------------
# Интерфейс командной строки
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
