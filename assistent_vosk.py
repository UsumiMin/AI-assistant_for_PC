import sys
import subprocess

try:
    import edge_tts
    import soundfile
    import sounddevice
    import vosk    
    import numpy
except ImportError:
    print("[Система]: Установка недостающих библиотек...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts", "soundfile", "sounddevice", "vosk"])

import queue
import json
import os
import zipfile
import urllib.request
import urllib.error
import asyncio
from io import BytesIO
import sounddevice as sd
import numpy as np
import soundfile as sf
from edge_tts import Communicate
from vosk import Model, KaldiRecognizer, SetLogLevel

VOICE = "ru-RU-SvetlanaNeural"

SetLogLevel(-1)

async def generate_anime_audio(text: str) -> bytes:
    communicate = Communicate(text, VOICE, pitch="+20Hz", rate="+10%")
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
        data, fs = sf.read(BytesIO(mp3_data), dtype='int16')
        sd.play(data, samplerate=fs)
        sd.wait()
    except Exception as e:
        print(f"\n[Ошибка TTS]: Не удалось озвучить текст ({e})", file=sys.stderr)

def progress_callback(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(int(downloaded * 100 / total_size), 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\r[Система]: Скачивание модели: {percent}% ({mb_downloaded:.1f} МБ из {mb_total:.1f} МБ)...", end="", flush=True)
    else:
        print(f"\r[Система]: Скачивание: {downloaded / (1024 * 1024):.1f} МБ...", end="", flush=True)

def download_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(script_dir, "1vosk-model-ru-0.22")
    
    if os.path.exists(model_path) and os.path.isdir(model_path):
        return model_path
    
    
    print("\n[Система]: Локальная модель не найдена. Начинаю скачивание с официального сайта Vosk...")
    
    url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    zip_path = os.path.join(script_dir, "model.zip")
    
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        
       
        urllib.request.urlretrieve(url, zip_path, reporthook=progress_callback)
        print("\n[Система]: Распаковка архива...")
        
        with zipfile.ZipFile(zip_path, 'r') as f:
            f.extractall(script_dir)
            
        
        extracted_folder = os.path.join(script_dir, "vosk-model-small-ru-0.22")
        
        if os.path.exists(extracted_folder):
            os.rename(extracted_folder, model_path)
            
    except Exception as e:
        print(f"\n[Критическая ошибка]: Не удалось скачать или распаковать модель ({e})")
        sys.exit(1)
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            
    print("[Система]: Модель успешно установлена и готова к работе!\n")
    return model_path

def speech_recognition_stream():
    model_path = download_model()
    
    print("[Система]: Загрузка движка Vosk...")
    model = Model(model_path)

    device_id = 9  
    
    
    device_info = sd.query_devices(device_id, 'input')
    native_samplerate = int(device_info['default_samplerate'])
    
    rec = KaldiRecognizer(model, native_samplerate)
    
    q = queue.Queue()
    
    def callback(indata, frames, time, status):
        if status:
            pass 
        q.put(bytes(indata))
    with sd.RawInputStream(samplerate=native_samplerate, blocksize=8000,
                          dtype='int16', channels=1, callback=callback, device=device_id):
        print("\n[Система]: Микрофон активен! Говорите...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get('text', '')
                if text:
                    yield text

def main():
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
    except Exception as e:
        print(f"\n[Критическая ошибка]: {e}")

if __name__ == '__main__':
    main()
