import winreg
from pathlib import Path
import os
def get_apps():
    start_menu_dirs = [
        Path(os.environ.get('ProgramData', 'C:\\ProgramData'), r'Microsoft\Windows\Start Menu\Programs'),
        Path(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Start Menu\Programs')
    ]
    
    apps = []
    for directory in start_menu_dirs:
        if not directory.exists():
            continue
        for lnk_path in directory.rglob('*.lnk'):
            app_name = lnk_path.stem.lower()
            if app_name and len(app_name) > 2:
                apps.append(app_name)
    
    return sorted(list(set(apps)))

if __name__ == "__main__":
    apps_list = get_apps()
    print("\n".join(apps_list))