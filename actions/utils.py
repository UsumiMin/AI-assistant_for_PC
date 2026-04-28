from contextlib import suppress

import psutil
import win32con
import win32gui
import win32process


def findWindowByProcessName(processName: str) -> int | None:
    window: int | None = None

    def enumCallback(hwnd: int, _: int | None) -> None:
        nonlocal window
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                proc = psutil.Process(pid)
                if proc.name() == processName:
                    window = hwnd

    win32gui.EnumWindows(enumCallback, None)
    return window


def activateWindow(hwnd: int) -> None:
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
