from actions.browser import runBrowser
from actions.calc import runCalc
from actions.change import change
from actions.clear_temp import clearTemp
from actions.create_file import create_file_on_desktop
from actions.dispatcher import Dispatcher
from actions.minimize_windows import minimizeAllWindows
from actions.recyclebin import emptyRecycleBin
from actions.run_app import run_app


def init_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()

    dispatcher.register('runBrowser', runBrowser)
    dispatcher.register('runCalc', runCalc)
    dispatcher.register('minimizeAllWindows', minimizeAllWindows)
    dispatcher.register('emptyRecycleBin', emptyRecycleBin)
    dispatcher.register('clearTemp', clearTemp)
    dispatcher.register('run', run_app)
    dispatcher.register('new', lambda target: create_file_on_desktop(filename=target))
    dispatcher.register('change', change)

    return dispatcher
