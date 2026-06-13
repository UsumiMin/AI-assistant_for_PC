"""
keyboard_layout.py — переключение раскладки клавиатуры в Windows.

Модуль умеет:
  * перечислять раскладки (языки ввода), установленные в системе;
  * переключать раскладку активного окна на указанный язык;
  * сообщать об ошибке, если запрошенного языка в системе нет.

Зависимостей нет — используется только стандартная библиотека (ctypes).
pywin32 для этой задачи не требуется (см. примечание в конце файла).

Работает только под Windows.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from dataclasses import dataclass

if sys.platform != 'win32':
    raise RuntimeError('Модуль keyboard_layout предназначен только для Windows')

__all__ = [
    'KeyboardLayout',
    'KeyboardLayoutError',
    'LayoutNotFoundError',
    'get_installed_layouts',
    'get_current_layout',
    'find_layout',
    'switch_layout',
]


# --------------------------------------------------------------------------- #
# Константы WinAPI
# --------------------------------------------------------------------------- #

WM_INPUTLANGCHANGEREQUEST = 0x0050

# LCType-флаги для GetLocaleInfoW
LOCALE_SISO639LANGNAME = 0x00000059  # 'en', 'ru'
LOCALE_SENGLISHLANGUAGENAME = 0x00001001  # 'English', 'Russian'
LOCALE_SNATIVELANGNAME = 0x00000004  # 'English', 'русский'
LOCALE_SNAME = 0x0000005C  # 'en-US', 'ru-RU'


# --------------------------------------------------------------------------- #
# Прототипы функций WinAPI
# --------------------------------------------------------------------------- #

HKL = wintypes.HANDLE  # дескриптор раскладки (в младшем слове — LANGID)

# WPARAM/LPARAM должны быть размером с указатель
_is64 = ctypes.sizeof(ctypes.c_void_p) == 8
WPARAM = ctypes.c_uint64 if _is64 else ctypes.c_uint32
LPARAM = ctypes.c_int64 if _is64 else ctypes.c_int32

_user32 = ctypes.WinDLL('user32', use_last_error=True)
_kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

_user32.GetKeyboardLayoutList.argtypes = [ctypes.c_int, ctypes.POINTER(HKL)]
_user32.GetKeyboardLayoutList.restype = ctypes.c_int

_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND

_user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD

_user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
_user32.GetKeyboardLayout.restype = HKL

_user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, WPARAM, LPARAM]
_user32.PostMessageW.restype = wintypes.BOOL

_kernel32.GetLocaleInfoW.argtypes = [
    wintypes.LCID,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.c_int,
]
_kernel32.GetLocaleInfoW.restype = ctypes.c_int


# --------------------------------------------------------------------------- #
# Исключения
# --------------------------------------------------------------------------- #


class KeyboardLayoutError(Exception):
    """Базовая ошибка модуля."""


class LayoutNotFoundError(KeyboardLayoutError):
    """Запрошенный язык не установлен в системе."""

    def __init__(self, language: str, available: list[KeyboardLayout]) -> None:
        self.language = language
        self.available = available
        names = ', '.join(sorted({f'{l.english_name} ({l.iso_code})' for l in available}))
        super().__init__(
            f"Раскладка для языка '{language}' не найдена. "
            f'Доступные языки: {names or "—"}'
        )


# --------------------------------------------------------------------------- #
# Модель данных
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class KeyboardLayout:
    """Описание одной раскладки (языка ввода)."""

    hkl: int  # полный дескриптор раскладки (HKL)
    langid: int  # LANGID = младшее слово HKL (= LCID языка)
    iso_code: str  # ISO 639, напр. 'en', 'ru'
    english_name: str  # англ. название языка, напр. 'Russian'
    native_name: str  # родное название языка, напр. 'русский'
    locale_name: str  # имя локали, напр. 'ru-RU'

    def __str__(self) -> str:
        return f'{self.english_name} ({self.locale_name}) [HKL=0x{self.hkl:08X}]'


# --------------------------------------------------------------------------- #
# Внутренние помощники
# --------------------------------------------------------------------------- #


def _get_locale_info(lcid: int, lctype: int) -> str:
    """Обёртка над GetLocaleInfoW: возвращает строку или '' при ошибке."""
    size = _kernel32.GetLocaleInfoW(lcid, lctype, None, 0)
    if size <= 0:
        return ''
    buf = ctypes.create_unicode_buffer(size)
    if _kernel32.GetLocaleInfoW(lcid, lctype, buf, size) <= 0:
        return ''
    return buf.value


def _build_layout(hkl_value: int) -> KeyboardLayout:
    langid = hkl_value & 0xFFFF
    return KeyboardLayout(
        hkl=hkl_value,
        langid=langid,
        iso_code=_get_locale_info(langid, LOCALE_SISO639LANGNAME),
        english_name=_get_locale_info(langid, LOCALE_SENGLISHLANGUAGENAME),
        native_name=_get_locale_info(langid, LOCALE_SNATIVELANGNAME),
        locale_name=_get_locale_info(langid, LOCALE_SNAME),
    )


# --------------------------------------------------------------------------- #
# Публичный API
# --------------------------------------------------------------------------- #


def get_installed_layouts() -> list[KeyboardLayout]:
    """Список раскладок (языков ввода), загруженных в системе."""
    count = _user32.GetKeyboardLayoutList(0, None)
    if count <= 0:
        raise KeyboardLayoutError('Не удалось получить число раскладок клавиатуры')

    buffer = (HKL * count)()
    written = _user32.GetKeyboardLayoutList(count, buffer)
    if written <= 0:
        raise ctypes.WinError(ctypes.get_last_error())

    layouts: list[KeyboardLayout] = []
    seen: set = set()
    for i in range(written):
        hkl_value = buffer[i] or 0
        if hkl_value in seen:
            continue
        seen.add(hkl_value)
        layouts.append(_build_layout(hkl_value))
    return layouts


def get_current_layout() -> KeyboardLayout | None:
    """Текущая раскладка активного окна (или None, если окна нет)."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    thread_id = _user32.GetWindowThreadProcessId(hwnd, None)
    hkl_value = _user32.GetKeyboardLayout(thread_id) or 0
    return _build_layout(hkl_value)


def find_layout(
    language: str,
    layouts: list[KeyboardLayout] | None = None,
) -> KeyboardLayout | None:
    """
    Найти установленную раскладку по названию языка.

    Принимает ISO-код ('ru'), имя локали ('ru-RU'),
    английское ('Russian') или родное ('русский') название языка.
    Регистр не важен.
    """
    if layouts is None:
        layouts = get_installed_layouts()

    needle = language.strip().casefold()
    for layout in layouts:
        candidates = {
            layout.iso_code.casefold(),
            layout.english_name.casefold(),
            layout.native_name.casefold(),
            layout.locale_name.casefold(),
            layout.locale_name.split('-')[0].casefold(),  # языковая часть локали
        }
        candidates.discard('')
        if needle in candidates:
            return layout
    return None


def switch_layout(language: str) -> KeyboardLayout:
    """
    Переключить раскладку активного окна на указанный язык.

    Возвращает выбранную раскладку.
    Бросает LayoutNotFoundError, если язык в системе не установлен.
    """
    layouts = get_installed_layouts()
    layout = find_layout(language, layouts)
    if layout is None:
        raise LayoutNotFoundError(language, layouts)

    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        raise KeyboardLayoutError('Не удалось определить активное окно')

    # Просим активное окно сменить язык ввода на нужный HKL.
    ok = _user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, layout.hkl)
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return layout


# --------------------------------------------------------------------------- #
# Запуск из командной строки
# --------------------------------------------------------------------------- #


def _main(argv: list[str]) -> int:
    if len(argv) < 2:
        print('Использование: python keyboard_layout.py <язык>\n')
        current = get_current_layout()
        if current is not None:
            print(f'Текущая раскладка: {current}\n')
        print('Установленные раскладки:')
        for layout in get_installed_layouts():
            print(f'  {layout.iso_code:<5} {layout.english_name} ({layout.locale_name})')
        return 0

    language = argv[1]
    try:
        layout = switch_layout(language)
    except LayoutNotFoundError as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 1
    except KeyboardLayoutError as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 2

    print(f'Раскладка переключена на: {layout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(_main(sys.argv))
