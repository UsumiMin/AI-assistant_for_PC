import asyncio
import json
import os
from io import BytesIO

import numpy as np
import sounddevice as sd
import soundfile as sf
from edge_tts import Communicate

VOICE = "ru-RU-SvetlanaNeural"

def _get_settings_path() -> str | None:
    app_name = "project"  # значение "name" из package.json
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    candidate = os.path.join(base, app_name, "settings.json")
    return candidate if os.path.exists(candidate) else None


def _load_volume() -> float:
    """Читает громкость из settings.json и возвращает float 0.0–1.0."""
    path = _get_settings_path()
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            raw = data.get("volume", 80)
            return max(0, min(int(raw), 100)) / 100.0
        except Exception:
            pass
    return 0.8  # умолчание


async def _generate_audio_stream(text: str) -> bytes:
    communicate = Communicate(text, VOICE, pitch="+20Hz", rate="+10%")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def say(text: str, volume: float | None = None) -> None:
    if not text.strip():
        return

    if volume is None:
        volume = _load_volume()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mp3_data = loop.run_until_complete(_generate_audio_stream(text))

        data, samplerate = sf.read(BytesIO(mp3_data))

        data = (np.array(data, dtype=np.float32) * volume)

        sd.play(data, samplerate=samplerate)
        sd.wait()
    except Exception as e:
        print(f"[Ошибка TTS]: {e}")
