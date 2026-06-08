import asyncio
from io import BytesIO
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from edge_tts import Communicate

VOICE = "ru-RU-SvetlanaNeural"

async def _generate_audio_stream(text: str) -> bytes:
    communicate = Communicate(text, VOICE, pitch="+25%", rate="+10%")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def say(text: str) -> None:
    if not text.strip():
        return
        
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mp3_data = loop.run_until_complete(_generate_audio_stream(text))
        
        audio_seg = AudioSegment.from_file(BytesIO(mp3_data), format="mp3")
        audio_seg = audio_seg.set_frame_rate(24000).set_channels(1)
        audio_np = np.array(audio_seg.get_array_of_samples(), dtype=np.int16)
        
        sd.play(audio_np, samplerate=24000)
        sd.wait()
    except Exception:
        pass
