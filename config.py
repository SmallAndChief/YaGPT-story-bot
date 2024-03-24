TOKEN = ''
folder_id = ""
GPT_MODEL = "yandexgpt-lite"
modelUri = f"gpt://{folder_id}/{GPT_MODEL}"
GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
STREAM = False
TEMPERATURE = 0.7
MAX_MODEL_TOKENS = 200
MAX_TOKENS_IN_SESSION = 1000
MAX_SESSIONS = 3
MAX_USERS = 3
DB_NAME = 'gpt_helper.db'
DB_TABLE_USERS_NAME = "users"
DB_TABLE_PROMTS_NAME = "promts"
SYSTEM_PROMPT = (
    "Ты пишешь историю вместе с человеком. "
    "Историю вы пишете по очереди. Начинаешь ты, а человек дополняет. "
    "Если это уместно, ты можешь добавлять в историю диалог между персонажами. "
    "Диалоги пиши с новой строки и отделяй тире. "
    "Не пиши никакого пояснительного текста в начале, а просто логично продолжай историю."
)
END_STORY = 'Напиши завершение истории c неожиданной развязкой. Не пиши никакой пояснительный текст от себя'
