import os
import sys

os.environ['VOSK_LOG_LEVEL'] = '-1'

import json
import queue
import urllib.request
import zipfile
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)

MODEL_NAME = "vosk-model-small-ru-0.22"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"

PRONUNCIATION_FIXES = {
    "повар поинт": "повер поинт",
    "поварпоинт": "повер поинт",
    "повара поинт": "повер поинт",
    "повер поинт": "повер поинт",
    "пауэр поинт": "повер поинт",
    "павер поинт": "повер поинт",
    "помер поинт": "повер поинт",
    "c тим": "стим",
    "тим": "стим",
    "сти": "стим",
    "эксель": "эксель",
    "карусель": "эксель",
    "цель": "эксель",
    "борд": "ворд",
    "лорд": "ворд",
    "млрд": "ворд",
    "ворота": "ворд",
    "храм": "хром",
    "хлам": "хром",
    "хром": "хром",
    "телеграм": "телеграмм",
    "тилиграм": "телеграмм",
    "телеграф": "телеграмм",
    "телега": "телеграмм",
    "тг": "телеграмм",
    "презентаций": "презентацию",
    "презентации": "презентацию",
    "презентация": "презентацию",
    "открытие спорт": "дискорд",
    "ди скотт": "дискорд",
    "скотт": "дискорд",
    "вещей код": "вижуал студио код",
    "вижу студио года": "вижуал студио код",
    "вижу студио год": "вижуал студио код",
    "вижу студию год": "вижуал студио код",
    "вижу студио код": "вижуал студио код",
    "ввести код": "вижуал студио код",
    "блютус": "блютуз",
    "блю туз": "блютуз",
    "блутуз": "блютуз",
    "громкость": "громкость",
    "громкасть": "громкость",
    "корзина": "корзину",
    "корзину": "корзину",
    "корзинка": "корзину",
}

def fix_recognition(text: str) -> str:

    text_lower = text.lower()
    for wrong, correct in PRONUNCIATION_FIXES.items():
        if wrong in text_lower:
            text_lower = text_lower.replace(wrong, correct)
    
    words = text_lower.split()
    fixed_words = []
    for word in words:
        if word in PRONUNCIATION_FIXES:
            fixed_words.append(PRONUNCIATION_FIXES[word])
        else:
            fixed_words.append(word)
    
    return " ".join(fixed_words)

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
                    
                    if not text:
                        continue
                    
                    fixed_text = fix_recognition(text)
                    
                    if fixed_text != text:
                        print(f"[Исправлено]: '{text}' -> '{fixed_text}'")
                    
                    yield fixed_text
                        
    except KeyboardInterrupt:
        print("\n[Система]: Остановка...")
    except Exception as e:
        print(f"\n[Ошибка]: {e}")

if __name__ == "__main__":
    for text in speech_recognition_stream():
        print(f"Распознано: {text}")