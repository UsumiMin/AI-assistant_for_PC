import queue, sys, json, os, zipfile, urllib.request
import sounddevice as sd
from vosk import Model, KaldiRecognizer

SAMPLE_RATE = 16000

def download_model():
    """Скачивает и распаковывает модель, если её нет"""
    model_path = "vosk-model-small-ru-0.22"
    if os.path.exists(model_path):
        return model_path

    print("Модель не найдена. Скачиваю...")
    url = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
    zip_path = "model.zip"

    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as f:
        f.extractall(".")

    os.remove(zip_path)
    print("Модель загружена!")
    return model_path

def main():
    model = Model(download_model())
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    print("\n Говорите \n")

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                          dtype='int16', channels=1, callback=callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result())['text']
                if text:
                    print(f"✓ {text}")
            else:
                partial = json.loads(rec.PartialResult()).get('partial', '')
                if partial:
                    print(f"  {partial}", end='\r')

if __name__ == '__main__':
    main()
