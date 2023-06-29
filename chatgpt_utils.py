import openai
import json

from config import OPENAI_API_KEY, logger
from decorators import retry

openai.api_key = OPENAI_API_KEY
MODEL_60 = 'gpt-3.5-turbo-0613'
MODEL_3 =  'gpt-3.5-turbo'


def extract_json(input_string):
    # Найдите индексы открывающей и закрывающей фигурных скобок
    start_index = input_string.find('{')
    end_index = input_string.rfind('}') + 1

    # Извлеките подстроку между этими индексами
    json_string = input_string[start_index:end_index]

    # Преобразуйте эту подстроку в JSON
    json_data = json.loads(json_string)

    return json_data


@retry((ValueError, json.JSONDecodeError), tries=3, delay=2, backoff=2)
def get_nutrition_info(prompt):
    response = openai.ChatCompletion.create(
        model=MODEL_3,
        messages=[
            {"role": "system", "content": '''Если запрос пользователя является вопросом, то ответь словом "вопрос"'''},
            {"role": "system", "content": '''Ответь словом "ошибка", если в сообщении от пользователя не упоминается никакая еда, напитки или питательные вещества'''},
            {"role": "system", "content": '''Прочитай список продуктов ниже и посчитай состав белков, жиров и углеводов. Посчитай точно насколько это возможно, при необходимости используй средние размеры продуктов или напитков, игнорируй тот факт что данные могут различаться.'''},
            {"role": "system", "content": '''Напиши мне ответ джейсоном вида {'fat': 100, 'protein': 100, 'carbs': 100, 'calories': 1000, 'text': 'тут еда и напитки из запроса'}, больше никакой другой информации, не делай никаких дополнительных комментариев или вопросов так как я буду брать твой ответ напрямую в базу данных.'''},
            {"role": "user", "content": prompt},
        ],
    )
    input_string = response.choices[0].message.content
    logger.info(f'function get_nutrition_info answer from API {input_string=}')
    if 'ошибка' in input_string.lower():
        return None
    elif 'вопрос' in input_string.lower():
        return get_food_smalltalk_answer(prompt)
    input_string = input_string.replace("'", '"')  # Замените одинарные кавычки на двойные для корректного JSON
    try:
        json_data = extract_json(input_string)
    except Exception as e:
        raise ValueError(f"Key '{input_string}' is cant be parsed as JSON")

    # Проверка ключей и типов данных
    required_keys = ['fat', 'protein', 'carbs', 'calories', 'text']
    for key in required_keys:
        if key not in json_data:
            raise ValueError(f"Key '{key}' is missing in the response")
        if key in ['fat', 'protein', 'carbs', 'calories']:
            try:
                json_data[key] = float(json_data[key])  # Преобразование к float
            except (ValueError, TypeError):
                raise ValueError(f"Value for '{key}' should be a number and convertible to float")
        elif key == 'text':
            if not isinstance(json_data[key], str):
                raise ValueError(f"Value for 'text' should be a string")
    return json_data


def get_food_smalltalk_answer(prompt):
    response = openai.ChatCompletion.create(
        model=MODEL_3,
        messages=[
            {"role": "system", "content": '''Если вопрос пользователя относится к теме питания, еды, спорта или диеты, то ответь так, как бы ответил опытный бот-диетолог. Если вопрос по другой теме, то ответь что ты пока не можешь отвечать на вопросы, которые не касаются питания, спорта или диеты'''},
            {"role": "user", "content": prompt},
        ],
    )
    answer_string = response.choices[0].message.content
    logger.info(f'function get_food_smalltalk_answer answer from API {answer_string=}')
    return answer_string