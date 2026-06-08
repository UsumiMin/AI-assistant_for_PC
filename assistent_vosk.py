import sys
import subprocess
import queue
import json
import os
import zipfile
import urllib.request
import urllib.error

from tts import say 
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)

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
    model_path = os.path.join(script_dir, "vosk-model-small-ru-0.22")
    
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
    device_id = None  
    
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
    assistant = MiniLMFunc()
    say("Система запущена. Я слушаю.")
    
    try:
        for final_text in speech_recognition_stream():
          
            json_str = assistant.get_json_response(final_text)
            data = json.loads(json_str)
            
            answer = data.get("answer", "Не понимаю вас.")
            say(answer)

            action = data.get("action")
            target = data.get("target")
            
            if action and action != "Talk":
                execute_action(action, target)
                
    except Exception as e:
        print(f"Ошибка в main: {e}")

def execute_action(action, target):
    print(f"Выполняю действие: {action} с целью: {target}")
    if action == "run":
        os.startfile(target)

if __name__ == '__main__':
    main()
