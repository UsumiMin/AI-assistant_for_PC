import queue
import sys
import json
import os
import zipfile
import urllib.request
import urllib.error
import asyncio
from io import BytesIO
import sounddevice as sd
import numpy as np
from pydub import AudioSegment
from edge_tts import Communicate
from vosk import Model, KaldiRecognizer, SetLogLevel

SAMPLE_RATE = 16000
VOICE = "ru-RU-SvetlanaNeural"

SetLogLevel(-1)
async def generate_anime_audio(text: str) -> bytes:
    communicate = Communicate(text, VOICE, pitch="+25%", rate="+10%")
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def say(text: str):
    print(f"[Ассистент]: {text}", flush=True)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        mp3_data = loop.run_until_complete(generate_anime_audio(text))
        
        audio_seg = AudioSegment.from_file(BytesIO(mp3_data), format="mp3")
        audio_seg = audio_seg.set_frame_rate(24000).set_channels(1)
        audio_np = np.array(audio_seg.get_array_of_samples(), dtype=np.int16)
    
        sd.play(audio_np, samplerate=24000)
        sd.wait()
    except Exception as e:
        print(f"\n[Ошибка TTS]: Не удалось озвучить текст ({e})", file=sys.stderr)

def progress_callback(block_num, block_size, total_size):

    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(int(downloaded * 100 / total_size), 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\rСкачивание модели: {percent}% ({mb_downloaded:.1f} из {mb_total:.1f} МБ)...", end="", flush=True)
    else:
        print(f"\rСкачивание модели: {downloaded / (1024 * 1024):.1f} МБ...", end="", flush=True)

def download_model():
    model_path = "vosk-model-small-ru-0.22"
    
    if os.path.exists(model_path):
        return model_path
    
    print("Модель не найдена. Начинаю установку...")
    url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    zip_path = "model.zip"
    
    try:
        urllib.request.urlretrieve(url, zip_path, reporthook=progress_callback)
        print("\nРаспаковка архива...")
        
        with zipfile.ZipFile(zip_path, 'r') as f:
            f.extractall(".")
            
    except urllib.error.URLError as e:
        print(f"\n[Ошибка сети]: Не удалось скачать модель ({e.reason}).")
        if os.path.exists(zip_path): os.remove(zip_path)
        sys.exit(1)
        
    except zipfile.BadZipFile:
        print("\n[Ошибка архива]: Файл поврежден. Попробуйте запустить снова.")
        if os.path.exists(zip_path): os.remove(zip_path)
        sys.exit(1)
        
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    print("Модель готова к работе!\n")
    return model_path

def speech_recognition_stream():
    model_path = download_model()
    model = Model(model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    q = queue.Queue()
    
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))
    
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                          dtype='int16', channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get('text', '')
                if text:
                    yield text


def main():
    print("[Система]: Голосовой движок запущен. Скажите что-нибудь...")
    
  
    say("Привет! Я готова к работе.")
    
    try:
        for final_text in speech_recognition_stream():
            print(f"[Вы сказали]: {final_text}")
            
            
            if "привет" in final_text or "здравствуй" in final_text:
                say("И тебе приветик! Рада тебя слышать.")
            elif "как дела" in final_text:
                say("Всё просто супер! Слушаю твои команды.")
            elif "пока" in final_text or "стоп" in final_text:
                say("До скорого!")
                break
            else:
                say(f"Ты сказал: {final_text}. Я тебя поняла!")
                
    except KeyboardInterrupt:
        print("\n[Система]: Работа завершена.")

if __name__ == '__main__':
    main()
