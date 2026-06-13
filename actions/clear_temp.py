import shutil
import tempfile
from pathlib import Path


def clearTemp(**_: str) -> None:
    temp_path = Path(tempfile.gettempdir())
    shutil.rmtree(temp_path)


if __name__ == '__main__':
    clearTemp()
