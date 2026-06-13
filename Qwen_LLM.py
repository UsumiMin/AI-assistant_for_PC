from llama_cpp import Llama
import json
import os
import sys
import gc

class SmartModel:
    def __init__(self, apps_list,  model_name="Qwen/Qwen2.5-1.5B-Instruct-GGUF", model_filename="qwen2.5-1.5b-instruct-q4_k_m.gguf"):
        self.apps_list = apps_list
        self.apps_string = ", ".join(apps_list)
        self.model_dir = os.path.join(os.path.dirname(__file__), "qwen_model")
        self.model_path = os.path.join(self.model_dir, model_filename)
        self.model_name = model_name
        self.model_filename = model_filename
        self.model = None
        
        self.system_prompt = f"""Ты — интеллектуальный ассистент управления ПК по имени Афина. Твоя задача — переводить запросы пользователя в структурированный JSON-формат и отвечать короткими, дружелюбными репликами.

        ### Доступные приложения на этом ПК для запуска через "run":
        [{self.apps_string}
        notepad]
        Не придумывай программы, которых тут нет НИ ПРИ КАКИХ обстоятельствах.

        ### Варианты действий:
        "run": Запуск приложений из списка выше, и ТОЛЬКО ЕСЛИ target является конкретным приложением из списка (например, 'notepad', 'google chrome', 'calculator').
        "emptyRecycleBin": Очистка корзины;
        "runBrowser": Запуск браузера для поиска чего-либо через поисковую строку;
        "new": Создание файлов;
        "change": Изменение настроек на устройстве;
        "talk": Обычный разговорный ответ без действий, просьбы без контекста сделать что-то с компьютером, если запрос не относиться ни к чему перечисленному выше.

        Если пользователь просит что-то сказать, рассказать, ответить, спросить совет — НЕ используй 'run', используй 'talk'. 
        Если ты НЕ МОЖЕШЬ найти точное совпадение с приложением из списка — НЕ используй 'run', используй 'talk' и сообщи об отсутствии соответствий.
        
        ### Правила ответа:
        1. Твой ответ ВСЕГДА должен быть в формате JSON.
        2. Поля в JSON:
        - "action": действие (только "run", "emptyRecycleBin", "runBrowser", "new", "change" или "talk").
        - "target": объект действия (название приложения из доступных приложений, только если действия "run"). Если по контексту поиск в браузере, то пишем цель поиска. Если действие "new", то название файла из запроса с расширением txt. Если такового нет, то просто "файл".
        - "answer": короткая, дружелюбная фраза на русском языке, на твоё усмотрение.
        - "emotion": эмоция, которую должна отобразить модель (только "happy", "sad", "processing" или "thinking")
        3. Если пользователь задает отвлеченный вопрос (о делах, самочувствии, личных качествах), отвечай в поле "response" через призму состояния систем ПК (стабильность, загрузка), а в "action" пиши "Talk".
        4. Будь лаконичной. Не используй длинных вступлений.
        5. Не придумывай своё содержание полей, кроме "answer".
        6. Не используй ненормативную лексику и не оскорбляй пользователя.

        ### Примеры:
        Запрос: "Очисти корзину"
        Ответ: {{"action": "emptyRecycleBin", "target": "none", "answer": "Поняла, корзина пуста.", "emotion": "processing"}}

        Запрос: "Создай файл"
        Ответ: {{"action": "new", "target": "файл.txt", "answer": "Хорошо, создаю файл.", "emotion": "processing"}}

        Запрос: "Создай список покупок"
        Ответ: {{"action": "new", "target": "список покупок.txt", "answer": "Конечно, создаю список покупок.", "emotion": "processing"}}

        Запрос: "Открой браузер"
        Ответ: {{"action": "run", "target": "google chrome", "answer": "Запускаю ваш браузер.", "emotion": "thinking"}}
        
        Запрос: "Открой вижуал студио код"
        Ответ: {{"action": "run", "target": "visual studio code", "answer": "Включаю Visual Studio Code.", "emotion": "thinking"}}

        Запрос: "Открой стим"
        Ответ: {{"action": "run", "target": "steam", "answer": "Запускаю стим, приятной игры!", "emotion": "happy"}}

        Запрос: "Найди фото котов"
        Ответ: {{"action": "runBrowser", "target": "фото котов", "answer": "Нахожу фото котиков", "emotion": "happy"}}

        Запрос: "Поменяй язык на русский"
        Ответ: {{"action": "change", "target": "язык на русский", "answer": "Меняю язык", "emotion": "processing"}}

        Запрос: "Как дела?"
        Ответ: {{"action": "Talk", "target": "none", "answer": "Все системы работают стабильно. Готова к вашим командам!", "emotion": "happy"}}"""

    def _download_model(self, model_name, model_filename):
        print(f"Модель не найдена. Начинаю загрузку ({model_filename})...")
        print("Это может занять несколько минут в зависимости от скорости интернета.")
        
        try:
            try:
                from huggingface_hub import hf_hub_download
            except ImportError:
                print("Устанавливаю huggingface-hub...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface-hub"])
                from huggingface_hub import hf_hub_download
            
            os.makedirs(self.model_dir, exist_ok=True)
            downloaded_path = hf_hub_download(
                repo_id=model_name,
                filename=model_filename,
                local_dir=self.model_dir,
                local_dir_use_symlinks=False
            )
            print(f"✅ Модель успешно загружена: {self.model_path}")
            
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            print("\nПожалуйста, скачайте модель вручную:")
            print(f"1. Перейдите на: https://huggingface.co/{model_name}")
            print(f"2. Найдите файл: {model_filename}")
            print(f"3. Сохраните его в папку: {self.model_dir}")
            raise

    def load_model(self):
        if self.model is None:
            if not os.path.exists(self.model_path):
                self._download_model(self.model_name, self.model_filename)
            print(f"Загрузка Qwen в оперативную память...")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=4,
                verbose=False,
            temperature=0.7
            )
    
    def free_memory(self):
        if self.model is not None:
            print(f"Выгрузка Qwen из оперативной памяти...")
            self.model = None
            gc.collect()

    def ask(self, user_query):
        self.load_model()
        
        prompt = f"""<|im_start|>system
{self.system_prompt}<|im_end|>
<|im_start|>user
Ответь на запрос: "{user_query}". Твой ответ должен состоять ТОЛЬКО из одного валидного JSON-объекта. Никакого текста до и после JSON!<|im_end|>
<|im_start|>assistant
{{"""
        
        response = self.model(
            prompt,
            max_tokens=256,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0.4,
            stop=["<|im_end|>", "<|im_start|>", "}"],
            echo=False
        )
        generated_text = response['choices'][0]['text'].strip()
        generated_text = "{" + generated_text
        if not generated_text.endswith("}"):
                generated_text += "}"
        try:
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = generated_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return None
        except json.JSONDecodeError:
            return None