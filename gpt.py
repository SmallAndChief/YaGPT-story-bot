import requests
import sqlite3
from config import modelUri, MAX_MODEL_TOKENS, TEMPERATURE, STREAM, GPT_URL, SYSTEM_PROMPT
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)


def create_prompt(user_data):
    prompt = SYSTEM_PROMPT
    prompt += (f"\nНапиши начало истории в стиле {user_data['genre']} "
               f"с главным героем {user_data['character']}. "
               f"Вот начальный сеттинг: \n{user_data['setting']}. \n"
               "Начало должно быть коротким, 1-3 предложения.\n")
    prompt += 'Не пиши никакие подсказки пользователю, что делать дальше. Он сам знает'
    return prompt


def create_new_token():
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}
    response = requests.get(url=metadata_url, headers=headers)
    logging.info("Создан новый iam_token")
    return response.json()


def send_request(url, headers, data):
    response = requests.post(url=url,
                             headers=headers,
                             json=data)
    logging.info("Запрос отправлен")
    return response


class GPT:
    def __init__(self):
        self.modelUri = modelUri
        self.MAX_MODEL_TOKENS = MAX_MODEL_TOKENS
        self.TEMPERATURE = TEMPERATURE
        self.STREAM = STREAM
        self.GPT_URL = GPT_URL

    def count_tokens_in_dialog(self, messages: sqlite3.Row, iam_token):
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'}
        data = {
            "modelUri": self.modelUri,
            "maxTokens": self.MAX_MODEL_TOKENS,
            "messages": []
        }
        for row in messages:
            data["messages"].append(
                {
                    "role": row[3],
                    "text": row[4]
                }
            )
        try:
            count = len(
                requests.post(
                    "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion",
                    json=data,
                    headers=headers
                ).json()["tokens"])
            logging.info(f"Количество токенов в диалоге {count}")
            return count
        except:
            logging.error("Ошибка с подсчетом токенов")
            return False

    @staticmethod
    def process_resp(response):
        try:
            if response.status_code == 200:
                text = response.json()["result"]["alternatives"][0]["message"]["text"]
                logging.info("Ответ от gpt успешно получен")
                return text
            else:
                error_message = 'Invalid response received: code: {}, message: {}'.format(response.status_code,
                                                                                          response.text)
                logging.error(error_message)
                return False
        except:
            logging.error("Непредвиденная ошибка")
            return False

    def make_promt(self, messages: sqlite3.Row, iam_token):
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'}
        data = {
            "modelUri": self.modelUri,
            "completionOptions": {
                "stream": self.STREAM,
                "temperature": self.TEMPERATURE,
                "maxTokens": self.MAX_MODEL_TOKENS
            },
            "messages": []
        }

        for row in messages:
            data["messages"].append(
                {
                    "role": row[3],
                    "text": row[4]
                }
            )
        resp = send_request(url=self.GPT_URL, headers=headers, data=data)
        return resp
