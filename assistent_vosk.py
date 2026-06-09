import sys
import queue
import json
import os
import zipfile
import urllib.request
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel
from tts import say 
from MiniLM import MiniLMFunc

SetLogLevel(-1)

def progress_callback(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(int(downloaded * 100 / total_size), 100)
        print(f"\r[Система]: Скачивание модели: {percent}%...", end="", flush=True)

def download_model():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_name = "vosk-model-small-ru-0.22"
    model_path = os.path.join(script_dir, model_name)
    
    if os.path.exists(model_path):
        return model_path
    
    print("\n[Система]: Локальная модель не найдена. Начинаю скачивание...")
    url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    zip_path = os.path.join(script_dir, "model.zip")
    
    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, zip_path, reporthook=progress_callback)
        
        print("\n[Система]: Распаковка...")
        with zipfile.ZipFile(zip_path, 'r') as f:
            f.extractall(script_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)
    except Exception as e:
        print(f"\n[Ошибка]: Не удалось скачать модель ({e})")
        sys.exit(1)
    return model_path

def speech_recognition_stream():
    model_path = download_model()
    model = Model(model_path)
    
    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])
    
    rec = KaldiRecognizer(model, samplerate)
    q = queue.Queue()
    
    def callback(indata, frames, time, status):
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, dtype='int16', 
                           channels=1, callback=callback):
        print("\n[Система]: Слушаю...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if 'text' in res and res['text']:
                    yield res['text']

def main():
    assistant = MiniLMFunc()
    say("Система запущена. Я слушаю.")
    print("[Система]: Ожидаю обращения к 'Афина'...")
    
    try:
        for final_text in speech_recognition_stream():
            text_lower = final_text.lower().strip()
            print(f"[Услышано]: '{text_lower}'")

            activation_keys = ["афина", "афину", "афине"]
            is_activated = any(key in text_lower for key in activation_keys)
            
            if is_activated:
                found_key = next(key for key in activation_keys if key in text_lower)
                clean_cmd = text_lower.replace(found_key, "").strip()
                
                print(f"[Распознано обращение к Афина]: '{clean_cmd}'")
                
                if clean_cmd:
                    json_str = assistant.get_json_response(clean_cmd)
                    data = json.loads(json_str)
                    
                    answer = data.get("answer", "Слушаю.")
                    print(f"[Ответ]: {answer}")
                    say(answer)
                else:
                    say("Да, я вас слушаю?")
                
    except Exception as e:
        print(f"[Критическая ошибка]: {e}")

if __name__ == '__main__':
    main()
