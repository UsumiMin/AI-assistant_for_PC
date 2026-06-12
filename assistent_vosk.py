import os
import sys
import json
import queue
import urllib.request
import zipfile
import sounddevice as sd
from vosk import Model, KaldiRecognizer

os.environ['VOSK_LOG_LEVEL'] = '-1'

MODEL_NAME = "vosk-model-small-ru-0.22"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def check_and_download_model():
    if not os.path.exists(MODEL_NAME):
        print(f"\n[Установка]: Модель Vosk не найдена. Скачиваю...")
        zip_path = f"{MODEL_NAME}.zip"
        
        try:
            urllib.request.urlretrieve(MODEL_URL, zip_path)
            print("[Установка]: Скачивание завершено! Распаковываю...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
                
            os.remove(zip_path)
            print("[Установка]: Модель успешно установлена!\n")
        except Exception as e:
            print(f"[Ошибка]: Не удалось скачать модель. {e}")
            sys.exit(1)
    else:
        print(f"[Загрузка]: Модель '{MODEL_NAME}' уже установлена.")

def speech_recognition_stream():
    check_and_download_model()
    
    print("[Загрузка]: Запуск распознавания речи (Vosk)...")
    model = Model(MODEL_NAME)
    rec = KaldiRecognizer(model, 16000)
    
    print("[Система]: Слушаю... (скажите 'Афина' для активации)")
    
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None, 
                               dtype='int16', channels=1, callback=callback):
            while True:
                data = q.get()
                
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    
                    if text:
                        yield text
                        
    except KeyboardInterrupt:
        print("\n[Система]: Остановка...")
    except Exception as e:
        print(f"\n[Ошибка]: {e}")

if __name__ == "__main__":
    for text in speech_recognition_stream():
        print(f"Распознано: {text}")