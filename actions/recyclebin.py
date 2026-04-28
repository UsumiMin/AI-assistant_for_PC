import logging

import pywintypes
from win32com.shell import shell, shellcon

logger = logging.getLogger(__name__)


def emptyRecycleBin() -> None:
    try:
        shell.SHEmptyRecycleBin(0, '', shellcon.SHERB_NOCONFIRMATION)
    except pywintypes.com_error:
        logger.info('Recycle bin is already empty')


if __name__ == '__main__':
    emptyRecycleBin()
