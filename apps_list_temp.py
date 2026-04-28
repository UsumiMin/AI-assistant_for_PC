import winreg

def get_apps():
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    reg_keys = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    apps = []

    for root in reg_keys:
        for path in paths:
            try:
                # Открывает ключ с флагом KEY_READ для безопасности
                with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as handler:
                    for i in range(winreg.QueryInfoKey(handler)[0]):
                        try:
                            key_name = winreg.EnumKey(handler, i)
                            with winreg.OpenKey(handler, key_name) as subkey:
                                try:
                                    name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                    if name:
                                        apps.append(name)
                                except OSError:
                                    continue
                        except OSError:
                            continue
            except Exception:
                continue

    return sorted(list(set(filter(None, apps))))

if __name__ == "__main__":
    apps_list = get_apps()
    print("\n".join(apps_list))