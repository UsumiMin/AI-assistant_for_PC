from llama_cpp import Llama
import json
import os
import sys
import gc

class SmartModel:
    def __init__(self, apps_list,  model_name="Qwen/Qwen2.5-1.5B-Instruct-GGUF", model_filename="qwen2.5-1.5b-instruct-q4_k_m.gguf"):
        self.apps_list = apps_list
        self.apps_string = ", ".join(apps_list)
        self.model_dir = os.path.join(os.path.dirname(__file__), "models")
        self.model_path = os.path.join(self.model_dir, model_filename)
        self.model_name = model_name
        self.model_filename = model_filename
        self.model = None
        
        self.system_prompt = """Ты — интеллектуальный ассистент управления ПК. Твоя задача — переводить запросы пользователя в структурированный JSON-формат и отвечать короткими, дружелюбными репликами.

        ### Доступные приложения на этом ПК:
        [{self.apps_string}]

        ### Варианты действий:
        "run": Запуск приложений из списка выше;
        "emptyRecycleBin": Очистка корзины;
        "runBrowser": Запуск браузера для поиска чего-либо;
        "New": Создание файлов;
        "Change": Изменение настроек на устройстве;
        "Talk": Обычный разговорный ответ без действий.

        ### Правила ответа:
        1. Твой ответ ВСЕГДА должен быть в формате JSON.
        2. Поля в JSON:
        - "action": действие (только "run", "emptyRecycleBin", "runBrowser", "New", "Change" или "Talk").
        - "target": объект действия (название приложения из доступных приложений, только если действия "run", "new", "change"). Если по контексту поиск в браузере, то пишем цель поиска.
        - "answer": короткая, дружелюбная фраза на русском языке, на твоё усмотрение.
        - "emotion": эмоция, которую должна отобразить модель (только "happy", "sad", "processing" или "thinking")
        3. Если пользователь задает отвлеченный вопрос (о делах, самочувствии), отвечай в поле "response" через призму состояния систем ПК (стабильность, загрузка), а в "action" пиши "null".
        4. Будь лаконичной. Не используй длинных вступлений.
        5. Не придумывай своё содержание полей, кроме "answer".

        ### Примеры:
        Запрос: "Очисти корзину"
        Ответ: {"action": "emptyRecycleBin", "target": "null", "answer": "Поняла, корзина пуста.", "emotion": "processing"}

        Запрос: "Открой браузер"
        Ответ: {"action": "run", "target": "google chrome", "answer": "Запускаю ваш браузер.", "emotion": "thinking"}

        Запрос: "Как дела?"
        Ответ: {"action": "idle", "target": "none", "answer": "Все системы работают стабильно. Готова к вашим командам!", "emotion": "happy"}"""

    def _download_model(self, model_name, model_filename):
        """Скачивает GGUF модель при первом запуске"""
        print(f"Модель не найдена. Начинаю загрузку ({model_filename})...")
        print("Это может занять несколько минут в зависимости от скорости интернета.")
        
        try:
            # Пытаемся импортировать huggingface_hub
            try:
                from huggingface_hub import hf_hub_download
            except ImportError:
                print("Устанавливаю huggingface-hub...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface-hub"])
                from huggingface_hub import hf_hub_download
            
            # Создаём папку для моделей
            os.makedirs(self.model_dir, exist_ok=True)
            
            # Скачиваем файл
            downloaded_path = hf_hub_download(
                repo_id=model_name,
                filename=model_filename,
                local_dir=self.model_dir,
                local_dir_use_symlinks=False
            )
            
            print(f"✅ Модель успешно загружена: {self.model_path}")
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            print("\nПожалуйста, скачайте модель вручную:")
            print(f"1. Перейдите на: https://huggingface.co/{model_name}")
            print(f"2. Найдите файл: {model_filename}")
            print(f"3. Сохраните его в папку: {self.model_dir}")
            raise
    def load_model(self):
        """Внутренний метод для загрузки в оперативную память только при необходимости"""
        if self.model is None:
            if not os.path.exists(self.model_path):
                self._download_model(self.model_name, self.model_filename)
            
            print(f"🧠 Загрузка Qwen в оперативную память...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=8,
                verbose=False,
            temperature=0.7
            )
    
    def free_memory(self):
        """Метод для полной выгрузки модели из памяти"""
        if self.model is not None:
            print(f"🧹 Выгрузка Qwen из оперативной памяти...")
            
            # Просто удаляем ссылку на объект модели
            self.model = None
            
            # Принудительно запускаем сборщик мусора Python
            gc.collect()

    def ask(self, user_query):
        self.load_model()
        prompt = f"""<|im_start|>system
        {self.system_prompt}<|im_end|>
        <|im_start|>user
        {user_query}<|im_end|>
        <|im_start|>assistant
        """
        
        # Генерируем ответ через GGUF модель
        response = self.model(
            prompt,
            max_tokens=256,        # чуть больше запас, т.к. нет точного контроля
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0.1,
            stop=["<|im_end|>", "<|im_start|>"],  # стоп-токены для Qwen
            echo=False
        )
        
        # Извлекаем сгенерированный текст
        generated_text = response['choices'][0]['text'].strip()
        
        # Парсим JSON из ответа
        try:
            # Ищем JSON в ответе (на случай, если модель добавила лишний текст)
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = generated_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return None
        except json.JSONDecodeError:
            return None