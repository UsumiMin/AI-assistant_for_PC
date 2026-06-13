from actions.change.bluetooth import disable_bluetooth, enable_bluetooth
from actions.change.lang import switch_layout
from actions.change.volume import MasterVolumeLevelManager


class UnexpectedTargetError(Exception):
    pass


mvl_mgr = MasterVolumeLevelManager()


def change(target: str) -> None:
    match target:
        case 'язык на английский':
            switch_layout('en')
        case 'язык на русский':
            switch_layout('ru')
        case 'увеличь громкость':
            mvl_mgr.increase()
        case 'уменьши громкость':
            mvl_mgr.decrease()
        case 'включи блютуз':
            enable_bluetooth()
        case 'выключи блютуз':
            disable_bluetooth()
        case _:
            raise UnexpectedTargetError(target)
