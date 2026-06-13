from pycaw.utils import AudioDevice, AudioUtilities


class MasterVolumeLevelManager:
    def __init__(self) -> None:
        self._mvl_before_mute: float | None = None  # master volume level before mute

    def increase(self, val: float = 0.1) -> None:
        device = self._get_device()
        self._set_master_volume_level_scalar(
            device=device,
            val=(self._get_master_volume_level_scalar(device) + val),
        )

    def decrease(self, val: float = 0.1) -> None:
        device = self._get_device()
        self._set_master_volume_level_scalar(
            device=device,
            val=(self._get_master_volume_level_scalar(device) - val),
        )

    def mute(self) -> None:
        if self._mvl_before_mute is not None:
            return
        device = self._get_device()
        self._mvl_before_mute = self._get_master_volume_level_scalar(device)
        self._set_master_volume_level_scalar(device=device, val=0)

    def unmute(self) -> None:
        if self._mvl_before_mute is None:
            return
        device = self._get_device()
        self._set_master_volume_level_scalar(device=device, val=self._mvl_before_mute)
        self._mvl_before_mute = None

    def set(self, val: float) -> None:
        device = self._get_device()
        self._set_master_volume_level_scalar(device=device, val=val)

    def _get_device(self) -> AudioDevice:
        return AudioUtilities.GetSpeakers()

    def _normalize(self, val: float) -> float:
        return max(0, min(val, 1))

    def _get_master_volume_level_scalar(self, device: AudioDevice) -> float:
        return device.EndpointVolume.GetMasterVolumeLevelScalar()

    def _set_master_volume_level_scalar(self, device: AudioDevice, val: float) -> None:
        device.EndpointVolume.SetMasterVolumeLevelScalar(self._normalize(val), None)


if __name__ == '__main__':
    import argparse

    mvl_mgr = MasterVolumeLevelManager()

    parser = argparse.ArgumentParser(
        prog='script.py',
        description='Manage master volume',
    )

    # Создаём подпарсеры - каждая подкоманда это отдельное "действие"
    subparsers = parser.add_subparsers(
        dest='command',  # в args.command сохранится имя выбранной подкоманды
        required=True,  # обязательно указать одну из команд
        help='Available commands',
    )

    # Подкоманда increase [value]
    increase_parser = subparsers.add_parser('increase', help='Increase volume')
    increase_parser.add_argument(
        'value',
        nargs='?',  # значение необязательно
        type=float,
        default=0.1,  # если не указано - по умолчанию 0.1
        help='Amount to increase (default: 0.1)',
    )

    # Подкоманда decrease [value]
    decrease_parser = subparsers.add_parser('decrease', help='Decrease volume')
    decrease_parser.add_argument(
        'value',
        nargs='?',
        type=float,
        default=0.1,
        help='Amount to decrease (default: 0.1)',
    )

    # Подкоманда mute (без аргументов)
    subparsers.add_parser('mute', help='Mute volume')

    # Подкоманда unmute (без аргументов)
    subparsers.add_parser('unmute', help='Unmute volume')

    args = parser.parse_args()

    # Вызов соответствующего метода
    if args.command == 'increase':
        mvl_mgr.increase(args.value)
    elif args.command == 'decrease':
        mvl_mgr.decrease(args.value)
    elif args.command == 'mute':
        mvl_mgr.mute()
    elif args.command == 'unmute':
        if mvl_mgr._get_master_volume_level_scalar(mvl_mgr._get_device()) == 0:
            mvl_mgr._mvl_before_mute = 0.5  # Для корректной работы unmute
        mvl_mgr.unmute()
