import os
from pathlib import Path

DEFAULT_DIR = Path(os.getenv('ProgramData'), r'Microsoft\Windows\Start Menu\Programs')


class AppNotFoundError(Exception):
    pass


def _find_app_executable(app_name: str) -> str | None:
    """Returns absolute path to app executable"""
    app_name = app_name.lower()
    for p in DEFAULT_DIR.walk():
        for f in p[2]:
            if app_name == f.lower().rsplit('.', maxsplit=1)[0]:
                return str(p[0] / f)
    return None


def run_app(target: str) -> None:
    executable = _find_app_executable(target)
    if executable is None:
        err_msg = f'Executable for app {target} not found'
        raise AppNotFoundError(err_msg)

    os.startfile(executable)


if __name__ == '__main__':
    run_app('notepad')
