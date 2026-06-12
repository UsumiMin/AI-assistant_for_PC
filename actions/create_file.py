r"""
Создание файла на рабочем столе текущего пользователя в Windows.

Определение пути к рабочему столу (по убыванию надёжности):
  1. shell.SHGetKnownFolderPath(FOLDERID_Desktop) -- основной способ.
     Сам учитывает перенаправление в OneDrive (Known Folder Move),
     локализованное имя папки ("Рабочий стол", "Bureau", ...) и любые
     пользовательские переносы. Перебор домашней директории не нужен.
  2. shell.SHGetFolderPath(CSIDL_DESKTOPDIRECTORY) -- для очень старых сборок pywin32.
  3. Реестр: HKCU\...\Explorer\User Shell Folders, значение "Desktop"
     (при активном переносе папок указывает на актуальное расположение).
  4. %USERPROFILE%\Desktop -- последний резерв.

Запись выполняется нативно (win32file.CreateFile/WriteFile/FlushFileBuffers),
а ошибки разбираются по кодам из модуля winerror.
"""

import logging
import os
import sys
import winreg
from datetime import datetime

import pywintypes
import win32api
import win32con
import win32file
import winerror
from win32com.shell import shell, shellcon

logger = logging.getLogger(__name__)

# FOLDERID_Desktop = {B4BFCC3A-DB2C-424C-B029-7FE99A87C641}
FOLDERID_DESKTOP: str = '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}'
# Вернуть путь без проверки наличия папки (не виснет на офлайн-OneDrive/сетевом диске).
KF_FLAG_DONT_VERIFY: int = getattr(shellcon, 'KF_FLAG_DONT_VERIFY', 0x00004000)


# --- Способы определения каталога рабочего стола -------------------------


def _desktop_via_known_folder() -> str | None:
    """Основной способ: SHGetKnownFolderPath(FOLDERID_Desktop) -- учитывает OneDrive и локализацию."""
    try:
        folderid = pywintypes.IID(FOLDERID_DESKTOP)
        return shell.SHGetKnownFolderPath(folderid, KF_FLAG_DONT_VERIFY, None)
    except Exception:
        return None  # старая pywin32 без этой функции / иной сбой -> следующий способ


def _desktop_via_csidl() -> str | None:
    """Запасной способ: SHGetFolderPath(CSIDL_DESKTOPDIRECTORY) -- физическая папка рабочего стола."""
    try:
        return shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOPDIRECTORY, 0, 0)
    except Exception:
        return None


def _desktop_via_registry() -> str | None:
    """Значение Desktop в User Shell Folders (актуально при переносе папок, в т. ч. OneDrive)."""
    key_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            raw, _ = winreg.QueryValueEx(key, 'Desktop')
        # Значение бывает REG_EXPAND_SZ с %USERPROFILE% и т. п.
        return win32api.ExpandEnvironmentStrings(raw)
    except Exception:
        return None


def _desktop_via_userprofile() -> str | None:
    """Последний резерв: %USERPROFILE%\\Desktop (без учёта OneDrive/локализации)."""
    home = os.environ.get('USERPROFILE') or os.path.expanduser('~')
    return os.path.join(home, 'Desktop') if home else None


def get_desktop_path() -> str:
    """Возвращает путь к рабочему столу, пробуя способы по убыванию надёжности."""
    for resolver in (
        _desktop_via_known_folder,
        _desktop_via_csidl,
        _desktop_via_registry,
        _desktop_via_userprofile,
    ):
        path = resolver()
        if path:
            return os.path.normpath(path)
    raise RuntimeError('Не удалось определить путь к рабочему столу ни одним способом.')


# --- Создание файла ------------------------------------------------------


def _unique_path(path: str) -> str:
    """Если файл уже существует, подбирает имя вида 'name (1).txt'."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f'{base} ({i}){ext}'
        if not os.path.exists(candidate):
            return candidate
        i += 1


def _describe_win_error(e: pywintypes.error, path: str) -> RuntimeError:
    """Преобразует pywintypes.error в понятное сообщение по коду winerror."""
    win = getattr(e, 'winerror', None)

    if win in (winerror.ERROR_DISK_FULL, winerror.ERROR_HANDLE_DISK_FULL):
        msg = 'На целевом диске недостаточно свободного места.'
    elif win == winerror.ERROR_ACCESS_DENIED:
        msg = (
            'Нет прав на запись в каталог рабочего стола. '
            'Возможны ограничения NTFS, групповая политика или блокировка антивирусом.'
        )
    elif win in (winerror.ERROR_PATH_NOT_FOUND, winerror.ERROR_FILE_NOT_FOUND):
        msg = (
            'Путь недоступен. Возможно, OneDrive офлайн '
            'или папка перенаправлена на отключённый сетевой/съёмный диск.'
        )
    elif win in (winerror.ERROR_FILE_EXISTS, winerror.ERROR_ALREADY_EXISTS):
        msg = 'Файл с таким именем уже существует.'
    elif win == winerror.ERROR_INVALID_NAME:
        msg = 'Недопустимое имя файла (запрещённые символы).'
    elif win == winerror.ERROR_FILENAME_EXCED_RANGE:
        msg = 'Слишком длинный путь или имя файла.'
    else:
        strerror = getattr(e, 'strerror', None) or str(e)
        msg = f'Ошибка ввода-вывода: {strerror}.'

    return RuntimeError(f'{msg}\n  Путь: {path}  [winerror={win}]')


def create_file_on_desktop(
    filename: str = 'hello_from_python.txt',
    content: str | None = None,
    overwrite: bool = False,
) -> str:
    """Создаёт файл на рабочем столе. Возвращает фактический путь созданного файла."""
    if content is None:
        content = f'Файл создан скриптом {datetime.now():%Y-%m-%d %H:%M:%S}\n'
    data = content.encode('utf-8')

    desktop = get_desktop_path()

    # Каталог рабочего стола отсутствует (офлайн-OneDrive, отключённый диск и т. п.).
    if not os.path.isdir(desktop):
        try:
            os.makedirs(desktop, exist_ok=True)
        except OSError as e:
            raise RuntimeError(
                f'Каталог рабочего стола недоступен и не может быть создан.\n'
                f'  Путь: {desktop}\n  Причина: {e.strerror or e}'
            ) from e

    target = os.path.join(desktop, filename)
    if not overwrite:
        target = _unique_path(target)

    # Быстрая проверка свободного места до записи.
    try:
        free = win32file.GetDiskFreeSpaceEx(desktop)[0]  # байт, доступных пользователю
        if free < len(data) + 4096:  # содержимое + небольшой запас
            raise RuntimeError(
                f'Недостаточно свободного места на диске рабочего стола.\n'
                f'  Путь: {desktop}\n  Свободно: {free} байт'
            )
    except pywintypes.error:
        pass  # на некоторых сетевых путях недоступно -- проверим уже при записи

    # Поддержка длинных путей (> 260 символов) через префикс \\?\
    abspath = os.path.abspath(target)
    write_path = abspath
    if len(abspath) >= 250 and not abspath.startswith('\\\\?\\'):
        write_path = '\\\\?\\' + abspath

    # CREATE_NEW -> ошибка, если файл уже существует; CREATE_ALWAYS -> перезапись.
    disposition = win32con.CREATE_ALWAYS if overwrite else win32con.CREATE_NEW
    handle = None
    try:
        handle = win32file.CreateFile(
            write_path,
            win32con.GENERIC_WRITE,
            0,  # без совместного доступа
            None,  # атрибуты безопасности по умолчанию
            disposition,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None,
        )
        win32file.WriteFile(handle, data)
        win32file.FlushFileBuffers(
            handle,
        )  # гарантируем запись на диск (точнее ловим "нет места")
    except pywintypes.error as e:
        raise _describe_win_error(e, target) from e
    finally:
        if handle is not None:
            handle.Close()

    return target


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    filename = argv[1] if len(argv) > 1 else 'hello_from_python.txt'

    try:
        path = create_file_on_desktop(filename)
    except RuntimeError as exc:
        logger.error(f'{exc}')
        return 1
    except Exception as exc:  # подстраховка на непредвиденное
        logger.exception(f'Непредвиденная ошибка: {type(exc).__name__}: {exc}')
        return 1

    logger.info(f'Файл создан: {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
