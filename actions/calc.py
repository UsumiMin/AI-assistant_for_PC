import psutil

from actions.utils import activateWindow, findWindowByProcessName

CALC_PROCESS_NAME = 'calc.exe'


def runCalc(**_: str) -> None:
    calcWindow: int | None = findWindowByProcessName(CALC_PROCESS_NAME)
    if calcWindow is None:
        psutil.Popen(CALC_PROCESS_NAME)
    else:
        activateWindow(calcWindow)


if __name__ == '__main__':
    runCalc()
