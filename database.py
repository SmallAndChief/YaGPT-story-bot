import sqlite3
import logging

from config import DB_NAME, DB_TABLE_PROMTS_NAME, DB_TABLE_USERS_NAME, MAX_USERS, MAX_SESSIONS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)


def execute_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    logging.info(f"DATABASE: Execute query: {sql_query}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)

    connection.commit()
    connection.close()


def execute_selection_query(sql_query, data=None, db_path=f'{DB_NAME}'):
    logging.info(f"DATABASE: Execute query: {sql_query}")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    if data:
        cursor.execute(sql_query, data)
    else:
        cursor.execute(sql_query)
    rows = cursor.fetchall()
    connection.close()
    return rows


def create_table1():
    sql_query = f'CREATE TABLE IF NOT EXISTS {DB_TABLE_USERS_NAME} ' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'genre TEXT, ' \
                f'character TEXT, ' \
                f'setting TEXT) '
    execute_query(sql_query)


def create_table2():
    sql_query = f'CREATE TABLE IF NOT EXISTS {DB_TABLE_PROMTS_NAME} ' \
                f'(id INTEGER PRIMARY KEY, ' \
                f'user_id INTEGER, ' \
                f'session_id INTEGER,' \
                f'role TEXT, ' \
                f'content TEXT) '
    execute_query(sql_query)


def insert_row(table_name, columns, values):
    sql_query = f"INSERT INTO {table_name} {columns} VALUES (?, ?, ?, ?)"
    execute_query(sql_query, values)


def is_value_in_table(table_name, column_name, value):
    sql_query = f'SELECT {column_name} FROM {table_name} WHERE {column_name} = ? LIMIT 1'
    rows = execute_selection_query(sql_query, [value])
    return len(rows) > 0


def update_row_value(user_id, column_name, new_value):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        sql_query = f'UPDATE {DB_TABLE_USERS_NAME} SET {column_name} = ? WHERE user_id = {user_id}'
        execute_query(sql_query, [new_value])
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")


def delete_user(user_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        sql_query = f'DELETE FROM {DB_TABLE_USERS_NAME} WHERE user_id = ?'
        execute_query(sql_query, [user_id])


def get_data_for_user(user_id):
    if is_value_in_table(DB_TABLE_USERS_NAME, 'user_id', user_id):
        sql_query = f'SELECT user_id, genre, character, setting ' \
                    f'FROM {DB_TABLE_USERS_NAME} where user_id = ? limit 1'
        row = execute_selection_query(sql_query, [user_id])[0]
        result = {
            'genre': row[1],
            'character': row[2],
            'setting': row[3],
        }
        return result
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
        return {
            'genre': "",
            'character': "",
            'setting': "",
        }


def get_dialogue_for_user(user_id, session_id):
    if is_value_in_table(DB_TABLE_PROMTS_NAME, 'user_id', user_id):
        sql_query = f"SELECT * FROM {DB_TABLE_PROMTS_NAME} WHERE user_id = ? AND session_id = ?;"
        rows = execute_selection_query(sql_query, [user_id, session_id])
        return rows
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
        return False


def get_story_for_user(user_id, session_id):
    if is_value_in_table(DB_TABLE_PROMTS_NAME, 'user_id', user_id):
        sql_query = (f"SELECT * FROM {DB_TABLE_PROMTS_NAME} WHERE user_id = ? AND session_id = ? AND role != ?;")
        rows = execute_selection_query(sql_query, [user_id, session_id, "system"])
        return rows
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
        return False


def get_session_id(user_id):
    if is_value_in_table(DB_TABLE_PROMTS_NAME, 'user_id', user_id):
        sql_query = f"SELECT session_id FROM {DB_TABLE_PROMTS_NAME} WHERE user_id = ? ORDER BY id DESC LIMIT 1;"
        session_id = execute_selection_query(sql_query, [user_id])[0]
        return session_id[0]
    else:
        logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
        return 0


def is_limit_users(db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    result = cursor.execute(f'SELECT DISTINCT user_id FROM {DB_TABLE_USERS_NAME};')
    count = 0
    for i in result:
        count += 1
    connection.close()
    return count >= MAX_USERS


def is_limit_sessions(user_id, db_path=f'{DB_NAME}'):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    result = cursor.execute(f'SELECT DISTINCT session_id FROM {DB_TABLE_PROMTS_NAME} WHERE user_id = ?;', [user_id])
    count = 0
    for i in result:
        count += 1
    connection.close()
    return count >= MAX_SESSIONS
