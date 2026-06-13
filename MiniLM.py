from sentence_transformers import SentenceTransformer, util
import torch
from rapidfuzz import process, distance
from transliterate import translit
from apps_list_temp import get_apps
import json
from Qwen_LLM import SmartModel
import logging
import os
import sys

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

class AppMatcher:
    def __init__(self):
        self.apps_list = get_apps()
        self.hard_coded_fixes = {
            "хром": "google chrome",
            "браузер": "google chrome",
            "телеграмм": "telegram desktop",
            "проводник": "explorer",
            "стим": "steam",
            "проводник": "explorer",
            "блокнот": "notepad",
            "заметки": "notepad",
            "заметочник": "notepad",
            "таблицы": "excel",
            "эксель": "excel",
            "ворд": "word",
            "документ": "word",
            "повер поинт": "powerpoint",
            "презентацию": "powerpoint",
            "текст": "notepad",
            "яндекс": "yandex",
            "вижуал студио код": "visual studio code"
        }

    def find(self, user_query):
        clean_query = user_query.lower()
        for v in ['открой', 'запусти', 'включи', 'пожалуйста']:
            clean_query = clean_query.replace(v, '').strip()
        query_variants = [clean_query, translit(clean_query, 'ru', reversed=True)]
        for ru, en in self.hard_coded_fixes.items():
            if ru in clean_query:
                query_variants.append(en)

        best_match = None
        max_score = 0

        for q in query_variants:
            result = process.extractOne(
                q,
                self.apps_list,
                scorer=distance.JaroWinkler.similarity
            )

            if result and result[1] > max_score:
                best_match = result[0]
                max_score = result[1]

        threshold = 0.6

        if max_score >= threshold:
            return best_match, max_score

        for ru, en in self.hard_coded_fixes.items():
            if ru in clean_query:
                return en, 1.0

        return None, max_score

class MiniLMFunc:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        # Указываем путь к локальной папке MiniLM
        minilm_path = os.path.join(base_path, 'minilm_model')

        # Загружаем модель из локальной папки
        self.model = SentenceTransformer(minilm_path)
        self.app_matcher = AppMatcher()
        self.smart_model = SmartModel(self.app_matcher.apps_list)
        self.ALLOWED_ACTIONS = {"run", "emptyRecycleBin", "runBrowser", "new", "change"}
        self.taxonomy = {
            "emptyRecycleBin": [
                "очисти корзину", "удали временные файлы", "почисти кэш",
                "освободи место на диске", "удалить мусор", "приберись в системе"
            ],
            "run": [
                "открой браузер", "запусти программу", "открой калькулятор", "включи плеер",
                "запусти игру", "открой блокнот", "запусти приложение"
            ],
            "runBrowser": [
                "найди в гугле", "перейди на сайт", "погугли как готовить", "найди",
                "найди рецепт в интернете", "открой сайт", "покажи курсы", "найди расписание"
            ],
            "new": [
                "создай текстовый документ", "сделай новую папку", "создай таблицу"
                "создай файл", "сделай заметку", "создай ворд", "создай презентацию"
            ],
            "change": [
                "сделай звук тише", "Увеличь громкость", "измени яркость", "поменяй обои",
                "включи блютуз", "включи ночной режим", "смени тему", "настрой сеть", "смени язык"
            ],
            "talk": [
                "как дела", "ты милая", "привет", "расскажи историю",
                "кто тебя создал", "поговори со мной", "спой песню"
            ]
        }

        self.category_embeddings = {}

        for category, phrases in self.taxonomy.items():
            self.category_embeddings[category] = self.model.encode(phrases, convert_to_tensor=True)

    def _validate_app_exists(self, app_name: str) -> bool:
        if not app_name:
            return False
        
        app_name_lower = app_name.lower()
        
        if app_name_lower in self.app_matcher.apps_list:
            return True
        
        for app in self.app_matcher.apps_list:
            if app_name_lower in app or app in app_name_lower:
                return True
        
        return False

    def _extract_target(self, text, category):
        if category == "run":
            target_app, score = self.app_matcher.find(text)
            return target_app if target_app else None

        if category == "runBrowser":
            clean_text = text.lower()
            for v in ["найди в гугле", "погугли", "найди в интернете", "найди", "открой", "покажи", "в гугле", "в браузере"]:
                clean_text = clean_text.replace(v, "").strip()
            return clean_text if clean_text else None

        if category == "new":
            clean_text = text.lower()
            for v in ["создай", "сделай"]:
                clean_text = clean_text.replace(v, "").strip()
            if clean_text is None:
                if category == "new":
                    clean_text = "файл"
            clean_text += ".txt"
            return clean_text if clean_text else None
        
        if category == "change":
            clean_text = text.lower()
            for v in ["сделай", "измени", "поменяй", "настрой"]:
                clean_text = clean_text.replace(v, "").strip()
            target, confidence = self.predict_change_command(clean_text)
            return target if target else None
        return None

    def predict(self, text):
        text_emb = self.model.encode(text, convert_to_tensor=True)
        results = {}
        for category, ref_embs in self.category_embeddings.items():
            scores = util.cos_sim(text_emb, ref_embs)
            results[category] = torch.max(scores).item()
        best_category = max(results, key=results.get)
        return best_category, results[best_category]
    
    def predict_change_command(self, text):
        """Определяет системную команду (громкость, язык, блютуз)"""
        system_commands = [
            'язык на английский',
            'язык на русский', 
            'увеличь громкость',
            'уменьши громкость',
            'включи блютуз',
            'выключи блютуз'
        ]
        text_emb = self.model.encode(text, convert_to_tensor=True)
        command_embs = self.model.encode(system_commands, convert_to_tensor=True)
        similarities = util.cos_sim(text_emb, command_embs)[0]
        
        best_idx = torch.argmax(similarities).item()
        best_command = system_commands[best_idx]
        confidence = similarities[best_idx].item()
        
        return best_command, confidence

    def get_json_response(self, text):
        category, confidence = self.predict(text)
        if (confidence < 0.6 or category == "talk") and self.smart_model:
            print(f"Низкая уверенность ({confidence:.2f}) или разговор. Обращаюсь к Qwen...")
            try:
                smart_res = self.smart_model.ask(text)
                if smart_res and isinstance(smart_res, dict):
                    answer = {
                        "action": smart_res.get("action"),
                        "target": smart_res.get("target"),
                        "answer": smart_res.get("answer"),
                        "emotion": smart_res.get("emotion"),
                        "source": "smart_llm"
                    }
                    if answer["action"] == "run":
                        target = answer.get("target")
                        if target and not self._validate_app_exists(target):
                            answer = {
                                "action": "talk",
                                "target": None,
                                "answer": f"Я не смогла найти программу '{target}'. Возможно, она не установлена или я не знаю такого названия. Попробуйте уточнить.",
                                "emotion": "sad",
                                "confidence": confidence,
                                "source": "minilm"
                            }
                    return json.dumps(answer, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Ошибка при вызове SmartModel: {e}. Откат к MiniLM.")
            finally:
                self.smart_model.free_memory()

        responses = {
            "emptyRecycleBin": ("Очищаю корзину.", "processing"),
            "run": ("Секунду, сейчас запущу...", "happy"),
            "runBrowser": ("Открываю браузер, ищу для вас информацию.", "thinking"),
            "new": ("Без проблем, сейчас всё создам.", "processing"),
            "change": ("Минутку, меняю настройки.", "processing"),
            "talk": ("Простите, я немного запуталась, повторите пожалуйста", "happy")
        }

        ans_text, emotion = responses.get(category, ("Я вас не совсем поняла.", "sad"))
        target = self._extract_target(text, category)
        final_action = category if category in self.ALLOWED_ACTIONS else None
        result = {
            "action": final_action,
            "target": target if category in ["run","new","change", "runBrowser"] else None,
            "answer": ans_text,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "source": "minilm"
        }

        return json.dumps(result, ensure_ascii=False, indent=4)



if __name__ == "__main__":
    """test_phrases = [
        "Почисти компьютер",
        "Приберись в системе",
        "Освободи место на диске",
        "Проведи уборку",
        "Открой браузер",
        "Открой проводник",
        "Включи видеоплеер",
        "Запусти блокнот",
        "Найди в интернете рецепт борща",
        "Погугли как сварить рис",
        "Найди ближайший магазин",
        "Покажи курс доллара",
        "Найди расписание поездов",
        "Запиши заметку",
        "Сделай текстовый файл",
        "Сохрани этот текст",
        "Сделай копию файла",
        "Создай презентацию",
        "Создай таблицу",
        "Поменяй язык на английский",
        "Включи тёмную тему",
        "Увеличь громкость",
        "Настрой сеть",
        "Включи блютуз",
        "Выключи блютуз"
    ]"""
    test_phrases = [
        "Расскажи как у тебя прошёл день",
        "Расскажи мне что такое 67"
    ]
    results = []
    assistant = MiniLMFunc()
    for phrase in test_phrases:
        res = assistant.get_json_response(phrase)
        results.append(res)

    for result in results:
        print(f"{result}")
