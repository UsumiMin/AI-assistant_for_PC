from transformers import AutoModelForCausalLM, AutoTokenizer
import json

class SmartModel:
    def __init__(self, apps_list, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype="auto", device_map="auto"
        )
        self.apps_string = ", ".join(apps_list)
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

    def ask(self, user_query):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]
        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=128,
            temperature=0.7,
            do_sample=True
        )
        response = self.tokenizer.batch_decode(generated_ids[:, model_inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
        
        try:
            return json.loads(response)
        except:
            return None