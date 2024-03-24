import logging
import time

from telebot import TeleBot
from telebot.types import BotCommand, ReplyKeyboardMarkup

from config import (TOKEN, DB_TABLE_USERS_NAME, DB_TABLE_PROMTS_NAME, MAX_TOKENS_IN_SESSION,
                    END_STORY)
from database import (create_table1, create_table2, delete_user, insert_row, update_row_value, get_data_for_user,
                      is_limit_users, is_limit_sessions, get_session_id, get_dialogue_for_user, get_story_for_user)
from gpt import GPT, create_new_token, create_prompt
from keyboards import (genre_markup, person_markup, setting_markup, end_button,
                       help_button, new_button, tokens_button, story_button, begin_button)

create_table1()
create_table2()

token_data = create_new_token()
expires_at = time.time() + token_data['expires_in']
iam_token = token_data['access_token']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)

gpt = GPT()
bot = TeleBot(token=TOKEN)

bot.set_my_commands([BotCommand('start', 'начало работы'),
                     BotCommand('help', 'инструкция'),
                     BotCommand('new_story', 'начать создание сюжета'),
                     BotCommand('end', 'закончить сюжет'),
                     BotCommand('all_tokens', 'потраченные токены'),
                     BotCommand('whole_story', 'весь сюжет'),
                     BotCommand('begin', 'начать генерить')])

STORY_CHOICES = {"genre": ["хоррор", "фантастика", "детектив", "комедия"],
                 "character": ["доктор холмс", "гарри поттер", "бабадук", "павел воля"],
                 "setting": ["город", "магическая академия", "заброшка", "парк развлечений"]}


@bot.message_handler(commands=['start'])
def start_message(message):
    logging.info('Отправка приветственного сообщения')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button)
    user_name = message.from_user.first_name
    bot.send_message(chat_id=message.chat.id,
                     text=f'Приветствую вас, {user_name}! Это GPT бот-сценарист. Для ознакомления введите /help.',
                     reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_message(message):
    logging.info('Отправка инструкции')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(new_button, tokens_button, story_button)
    bot.send_message(chat_id=message.chat.id,
                     text=("Данный бот предлагает вам выбрать жанр, персонажа и сеттинг, чтобы придумать"
                           "какую-то историю при помощи YaGPT.\n/new_story - начать придумывать историю."
                           "Всего возможно придумать 3 истории ограничены в 1000 токенов.\n/end - завершить историю."
                           "\nПосле всех выборов /begin - начать придумывание сюжета(после /new_story)."
                           "\n/all_tokens - количество использованных токенов за всё время."
                           "\n/whole_story - выводит всю историю целиком."
                           "Во время создания истории бот присылает часть её, вы её дополняете и бот "
                           "присылает продолжение. Так до тех пор, пока не закончатся токены или введётся /end"
                           "\nПродолжая сюжет не увлекайтесь, иначе можете попусту потратить токены."),
                     reply_markup=markup)


@bot.message_handler(commands=['new_story'])
def new_story_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if is_limit_users():
        bot.send_message(chat_id,
                         text="Достигнут лимит пользователей. Вы не сможете воспользоваться ботом.")
        return
    elif is_limit_sessions(user_id):
        bot.send_message(chat_id,
                         text="Достигнут лимит историй. Вы не сможете воспользоваться ботом.")
        return
    logging.info(f'Начата ноовая история {user_id}')
    delete_user(user_id)
    insert_row(DB_TABLE_USERS_NAME, '(user_id, genre, character, setting)', (user_id, "", "", ""))
    bot.send_message(chat_id,
                     text="Выберите жанр истории с помощью кнопок",
                     reply_markup=genre_markup)
    bot.register_next_step_handler(message, genre_message)


def genre_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    genre = message.text
    if not genre.lower() in STORY_CHOICES["genre"]:
        logging.warning(f'Неудачно выбран жанр {user_id}')
        bot.send_message(chat_id,
                         text="Такого жанра нет. Выберите жанр с помощью кнопок",
                         reply_markup=genre_markup)
        bot.register_next_step_handler(message, genre_message)
    else:
        update_row_value(user_id, "genre", genre)
        bot.send_message(chat_id,
                         text="Выберите персонажа с помощью кнопок",
                         reply_markup=person_markup)
        logging.info(f'Выбран жанр {user_id}')
        bot.register_next_step_handler(message, character_message)


def character_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    character = message.text
    if not character.lower() in STORY_CHOICES["character"]:
        logging.warning(f'Неудачно выбран персонаж {user_id}')
        bot.send_message(chat_id,
                         text="Такого персонажа нет. Выберите персонажа с помощью кнопок",
                         reply_markup=person_markup)
        bot.register_next_step_handler(message, character_message)
    else:
        update_row_value(user_id, "character", character)
        bot.send_message(chat_id,
                         text="Выберите сеттинг с помощью кнопок",
                         reply_markup=setting_markup)
        logging.info(f'Выбран персонаж {user_id}')
        bot.register_next_step_handler(message, setting_message)


def setting_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    setting = message.text
    if not setting.lower() in STORY_CHOICES["setting"]:
        logging.warning(f'Неудачно выбран сеттинг {user_id}')
        bot.send_message(chat_id,
                         text="Такого сеттинга нет. Выберите сеттинг с помощью кнопок",
                         reply_markup=setting_markup)
        bot.register_next_step_handler(message, setting_message)
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(begin_button)
        update_row_value(user_id, "setting", setting)
        bot.send_message(chat_id,
                         text="Введите /begin чтобы начать историю",
                         reply_markup=markup)
        logging.info(f'Выбран сеттинг {user_id}')
        session_id = get_session_id(user_id=user_id) + 1
        data = get_data_for_user(user_id=user_id)
        system_content = create_prompt(data)
        insert_row(DB_TABLE_PROMTS_NAME, "(user_id, session_id, role, content)",
                   (user_id, session_id, "system", system_content))


@bot.message_handler(commands=['all_tokens'])
def tokens_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button, new_button)
    chat_id = message.chat.id
    user_id = message.from_user.id
    session_id = get_session_id(user_id=user_id)
    if session_id == 0:
        bot.send_message(chat_id,
                         text="Вы еще ничего не начали. Введите /help",
                         reply_markup=markup)
        return
    tokens = 0
    global expires_at, iam_token, token_data
    if expires_at < time.time():
        token_data = create_new_token()
        expires_at = time.time() + token_data['expires_in']
        iam_token = token_data['access_token']
    for session in range(session_id):
        tokens += gpt.count_tokens_in_dialog(get_dialogue_for_user(user_id, session + 1), iam_token)
    bot.send_message(chat_id,
                     text=f"Количество токенов использовано {tokens}",
                     reply_markup=markup)


@bot.message_handler(commands=['whole_story'])
def whole_story_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button, new_button)
    chat_id = message.chat.id
    user_id = message.from_user.id
    session_id = get_session_id(user_id=user_id)
    if session_id == 0:
        bot.send_message(chat_id,
                         text="Вы еще ничего не начали. Введите /help",
                         reply_markup=markup)
        return
    try:
        rows = get_story_for_user(user_id, session_id)
        story = "История:\n"
        for row in rows:
            story += row[4]
        bot.send_message(chat_id,
                         text=story,
                         reply_markup=markup)
    except:
        bot.send_message(chat_id,
                         text="Неизвестная ошибка. Введите /help",
                         reply_markup=markup)


@bot.message_handler(commands=['begin'])
def story_message(message):
    logging.info("Начата история")
    gpt_request(message, begin=True)


def gpt_request(message, begin=False):
    end = False
    warning = ""
    chat_id = message.chat.id
    user_id = message.from_user.id
    session_id = get_session_id(user_id=user_id)
    global expires_at, iam_token, token_data
    if expires_at < time.time():
        token_data = create_new_token()
        expires_at = time.time() + token_data['expires_in']
        iam_token = token_data['access_token']
    if not begin:
        content = message.text
        if content == "/end":
            end = True
            insert_row(DB_TABLE_PROMTS_NAME, "(user_id, session_id, role, content)",
                       (user_id, session_id, "system", END_STORY))
        else:
            insert_row(DB_TABLE_PROMTS_NAME, "(user_id, session_id, role, content)",
                       (user_id, session_id, "user", content))
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        messages = get_dialogue_for_user(user_id, session_id)
        tokens = gpt.count_tokens_in_dialog(messages, iam_token)
        if tokens >= MAX_TOKENS_IN_SESSION:
            markup.add(help_button, new_button)
            bot.send_message(chat_id,
                             text="Превышен лимит токенов на историю. Начните снова /new_story",
                             reply_markup=markup)
            return
        elif tokens + 150 >= MAX_TOKENS_IN_SESSION:
            warning = "\nТокены кончаются. Советую закончить историю."
        resp = gpt.make_promt(messages, iam_token)
        answer = gpt.process_resp(resp)
        if answer:
            markup.add(end_button, help_button)
            bot.send_message(chat_id,
                             text=answer + warning,
                             reply_markup=markup)
            insert_row(DB_TABLE_PROMTS_NAME, "(user_id, session_id, role, content)",
                       (user_id, session_id, "assistant", answer))
            if end:
                return
            bot.register_next_step_handler(message, gpt_request)
        else:
            markup.add(help_button, begin_button, new_button)
            bot.send_message(chat_id,
                             text=("Произошла ошибка. Попробуйде подождать и ввести /begin. Или начните снова"
                                   " /new_story"),
                             reply_markup=markup)
    except:
        bot.send_message(chat_id,
                         text="Произошла ошибка. Попробуйде подождать и ввести /begin. Или начните снова /new_story",
                         reply_markup=markup)


@bot.message_handler(commands=['debug'])
def debug_message(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(content_types=['text'])
def text_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button)
    bot.send_message(chat_id=message.chat.id,
                     text='Я не понимаю чего вы хотите. Введите /help.',
                     reply_markup=markup)
    logging.info(f'Неизвестная команда от {message.from_user.id}')


bot.infinity_polling()
