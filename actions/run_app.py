import os
from pathlib import Path

DEFAULT_DIRS = (
    Path(os.environ.get('ProgramData'), r'Microsoft\Windows\Start Menu\Programs'),
    Path(os.environ.get('APPDATA'), r'Microsoft\Windows\Start Menu\Programs'),
)


class AppNotFoundError(Exception):
    pass


def _find_app_executable(app_name: str) -> str | None:
    """Returns absolute path to app executable"""
    app_name = app_name.lower()
    for d in DEFAULT_DIRS:
        for p in d.walk():
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
    import sys

    run_app(sys.argv[1])
