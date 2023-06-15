import openai
import json
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


def extract_json(input_string):
    # Найдите индексы открывающей и закрывающей фигурных скобок
    start_index = input_string.find('{')
    end_index = input_string.rfind('}') + 1

    # Извлеките подстроку между этими индексами
    json_string = input_string[start_index:end_index]

    # Преобразуйте эту подстроку в JSON
    json_data = json.loads(json_string)

    return json_data


def get_nutrition_info(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": '''Напиши мне ответ джейсоном вида {'fat': 100, 'protein': 100, 'carbs': 100, 'calories': 1000, 'text': 'тут текст запроса'}, больше никакой другой информации, так как я буду брать твой ответ напрямую в базу данных. Прочитай список продуктов ниже и посчитай состав белков, жиров и углеводов. ПОсчитай точно насколько это возможно, при необходимости используй средние размеры продуктов'''},
            {"role": "user", "content": prompt},
        ],
    )
    input_string = response.choices[0].message.content
    input_string = input_string.replace("'", '"')  # Замените одинарные кавычки на двойные для корректного JSON
    json_data = extract_json(input_string)

    return json_data
