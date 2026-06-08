import asyncio
from io import BytesIO
import sounddevice as sd
import soundfile as sf
from edge_tts import Communicate

VOICE = "ru-RU-SvetlanaNeural"

async def _generate_audio_stream(text: str) -> bytes:
    communicate = Communicate(text, VOICE, pitch="+20Hz", rate="+10%")
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
    
        data, samplerate = sf.read(BytesIO(mp3_data))
        
        sd.play(data, samplerate=samplerate)
        sd.wait()
    except Exception as e:
        print(f"[Ошибка TTS]: {e}")
