import win32com.client


def minimizeAllWindows() -> None:
    shell = win32com.client.Dispatch('Shell.Application')
    shell.MinimizeAll()


if __name__ == '__main__':
    minimizeAllWindows()
