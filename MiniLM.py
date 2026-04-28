from sentence_transformers import SentenceTransformer, util
import torch
from rapidfuzz import process, distance
from transliterate import translit
from apps_list_temp import get_apps
import json
from Qwen_LLM import SmartModel

class AppMatcher:
    def __init__(self, apps_list):
        self.apps_list = apps_list
        self.hard_coded_fixes = {
            "хром": "google chrome",
            "браузер": "google chrome",
            "телега": "telegram desktop",
            "тг": "telegram desktop",
            "проводник": "explorer",
            "стим": "steam",
            "проводник": "explorer",
            "блокнот": "notepad"
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
        return None, max_score
    
class MiniLMFunc:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        apps_list = get_apps()
        self.app_matcher = AppMatcher(apps_list)
        self.smart_model = SmartModel(apps_list)

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
                "найди в гугле", "перейди на сайт", "погугли как готовить", 
                "найди рецепт в интернете", "открой сайт", "покажи курсы", "найди расписание"
            ],
            "New": [
                "создай текстовый документ", "сделай новую папку", "создай таблицу"
                "создай файл", "сделай заметку", "создай ворд", "создай презентацию"
            ],
            "Change": [
                "сделай звук тише", "Увеличь громкость", "измени яркость", "поменяй обои", 
                "включи блютуз", "включи ночной режим", "смени тему", "настрой сеть", "смени язык"
            ],
            "Talk": [
                "как дела", "ты милая", "привет", "расскажи историю", 
                "кто тебя создал", "поговори со мной", "спой песню"
            ]
        }
        
        self.category_embeddings = {}
        
        for category, phrases in self.taxonomy.items():
            self.category_embeddings[category] = self.model.encode(phrases, convert_to_tensor=True)

    def _extract_target(self, text, category):
        if category == "run":
            target_app, score = self.app_matcher.find(text)
            return target_app if target_app else "неизвестное приложение"
        if category == "runBrowser":
            clean_text = text.lower()
            for v in ["найди в гугле", "погугли", "найди в интернете", "найди"]:
                clean_text = clean_text.replace(v, "").strip()
            return clean_text
        if category in ["New", "Change"]:
            clean_text = text.lower()
            for v in ["создай", "сделай", "измени", "поменяй", "настрой"]:
                clean_text = clean_text.replace(v, "").strip()
            return clean_text
        
        return "null"
    
    def predict(self, text):
        text_emb = self.model.encode(text, convert_to_tensor=True)
        results = {}
        for category, ref_embs in self.category_embeddings.items():
            scores = util.cos_sim(text_emb, ref_embs)
            results[category] = torch.max(scores).item()
        best_category = max(results, key=results.get)
        return best_category, results[best_category]
    
    def get_json_response(self, text):
        category, confidence = self.predict(text)
        if confidence < 0.6 and self.smart_model:
            print(f"Низкая уверенность ({confidence:.2f}). Обращаюсь к Qwen...")
            smart_res = self.smart_model.ask(text)
            if smart_res:
                return json.dumps({
                    "action": smart_res.get("action"),
                    "target": smart_res.get("target"),
                    "answer": smart_res.get("answer"),
                    "emotion": smart_res.get("emotion"),
                    "source": "smart_llm"
                }, ensure_ascii=False, indent=4)
            
        responses = {
            "emptyRecycleBin": ("Очищаю систему.", "processing"),
            "run": ("Секунду, сейчас запущу...", "happy"),
            "runBrowser": ("Открываю браузер, ищу для вас информацию.", "thinking"),
            "New": ("Без проблем, сейчас всё создам.", "processing"),
            "Change": ("Минутку, меняю настройки.", "processing"),
            "Talk": ("Я всегда рада поболтать!", "happy")
        }
        
        ans_text, emotion = responses.get(category, ("Я вас не совсем поняла.", "sad"))
        target = self._extract_target(text, category)

        result = {
            "action": category if category != "Talk" else "null",
            "target": target if category in ["run","New","Change"] else "null",
            "answer": ans_text,
            "emotion": emotion,
            "confidence": confidence
        }
        
        return json.dumps(result, ensure_ascii=False, indent=4)



if __name__ == "__main__":
    test_phrases = [
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
    ]
    results = []
    assistant = MiniLMFunc()
    for phrase in test_phrases:
        res = assistant.get_json_response(phrase)
        results.append(res)

    for result in results:
        print(f"{result}")