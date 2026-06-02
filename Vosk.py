import queue, sys, json, os, zipfile, urllib.request
import urllib.error
import sounddevice as sd
# Импортируем SetLogLevel для отключения системного спама Vosk
from vosk import Model, KaldiRecognizer, SetLogLevel

SAMPLE_RATE = 16000

SetLogLevel(-1)

def progress_callback(block_num, block_size, total_size):
    """Отображает индикатор скачивания в консоли"""
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(int(downloaded * 100 / total_size), 100)
        mb_downloaded = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\rСкачивание модели: {percent}% ({mb_downloaded:.1f} из {mb_total:.1f} МБ)...", end="", flush=True)
    else:
        print(f"\rСкачивание модели: {downloaded / (1024 * 1024):.1f} МБ...", end="", flush=True)

def download_model():
    """Скачивает и распаковывает модель с обработкой ошибок"""
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
    """Функция-генератор. Возвращает только четко завершенные финальные фразы."""
    model_path = download_model()
    model = Model(model_path)
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    q = queue.Queue()
    
    def callback(indata, frames, time, status):
        # Ошибки переполнения буфера аудиокарты отправляем в скрытый поток ошибок sys.stderr
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))
    
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                          dtype='int16', channels=1, callback=callback):
        while True:
            data = q.get()
            # AcceptWaveform возвращает True, только когда распознана пауза и фраза закончена
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get('text', '')
                if text:
                    # Возвращаем исключительно финальный текст
                    yield text

def main():
    try:
        # В цикле обрабатываются только завершенные фразы
        for final_text in speech_recognition_stream():
            # Выводим чистый текст на экран
            print(final_text, flush=True)
    except KeyboardInterrupt:
        pass # Корректный выход по Ctrl+C без системных ошибок в консоли

if __name__ == '__main__':
    main()
