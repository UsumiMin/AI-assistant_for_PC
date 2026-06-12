import shlex
import urllib.parse
import winreg
from pathlib import Path

import psutil

from actions.utils import activateWindow, findWindowByProcessName

DEFAULT_SEARCH_ENGINE = 'https://www.google.com/search?q='

def getBrowserNameInRegistry() -> str:
    registry_path = (
        r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations\https\UserChoice'
    )
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
        return str(winreg.QueryValueEx(key, 'ProgId')[0])


def getBrowserExePath(name: str) -> str:
    registry_path = rf'{name}\shell\open\command'
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, registry_path) as key:
        return shlex.split(str(winreg.QueryValueEx(key, '')[0]))[0]


def runBrowser(target: str | None = None) -> None:
    browserExePath: Path = Path(getBrowserExePath(getBrowserNameInRegistry()))

    browserWindow: int | None = findWindowByProcessName(browserExePath.name)
    #if browserWindow is None:
    if target:
            psutil.Popen(
                [
                    browserExePath,
                    DEFAULT_SEARCH_ENGINE + urllib.parse.quote(string=target, safe=''),
                ],
            )
    else:
            psutil.Popen(browserExePath)
   # else:
   #     activateWindow(browserWindow)


if __name__ == '__main__':
    runBrowser()
