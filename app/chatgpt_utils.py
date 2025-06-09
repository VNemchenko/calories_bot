from openai import OpenAI
import json

from config import OPENAI_API_KEY, logger
from decorators import retry

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = 'gpt-4o-mini'

nutrition_function = {
    "name": "get_nutrition_info",
    "description": "Вычисляет общее количество жиров, белков, углеводов и калорий из списка продуктов.",
    "parameters": {
        "type": "object",
        "properties": {
            "fat": {"type": "number", "description": "Общее количество жиров в граммах"},
            "protein": {"type": "number", "description": "Общее количество белков в граммах"},
            "carbs": {"type": "number", "description": "Общее количество углеводов в граммах"},
            "calories": {"type": "number", "description": "Общее количество калорий"},
            "text": {"type": "string", "description": "Продукты и напитки из запроса пользователя"},
        },
        "required": ["fat", "protein", "carbs", "calories", "text"],
    },
}

@retry((ValueError, json.JSONDecodeError), tries=3, delay=2, backoff=2)
def get_nutrition_info(prompt):
    system_message = (
        "Ты — опытный бот-диетолог. Если сообщение пользователя является вопросом, ответь строго словом 'вопрос'. "
        "Если пользователь не упомянул еду, напитки или питательные вещества, ответь словом 'ошибка'. "
        "Изучи список продуктов ниже и вычисли белки, жиры, углеводы и калории. "
        "Старайся оценивать максимально точно, при необходимости ориентируйся на средние размеры порций и игнорируй различия в источниках. "
        "Верни только JSON-объект, соответствующий функции 'get_nutrition_info', без лишнего текста."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        functions=[nutrition_function],
        function_call={"name": "get_nutrition_info"},
    )

    message = response.choices[0].message
    logger.info(f'function get_nutrition_info answer from API {message=}')

    if message.function_call:
        function_call = message.function_call
        arguments = function_call.arguments or "{}"
        try:
            json_data = json.loads(arguments)
        except json.JSONDecodeError:
            raise ValueError(f"Arguments could not be parsed as JSON: {arguments}")

        required_keys = ['fat', 'protein', 'carbs', 'calories', 'text']
        for key in required_keys:
            if key not in json_data:
                raise ValueError(f"Key '{key}' is missing in the response")
            if key in ['fat', 'protein', 'carbs', 'calories']:
                try:
                    json_data[key] = float(json_data[key])
                except (ValueError, TypeError):
                    raise ValueError(f"Value for '{key}' should be a number and convertible to float")
            elif key == 'text':
                if not isinstance(json_data[key], str):
                    raise ValueError(f"Value for 'text' should be a string")
        return json_data
    else:
        content = message.content or ""
        if 'ошибка' in content.lower():
            return None
        elif 'вопрос' in content.lower():
            return get_food_smalltalk_answer(prompt)
        else:
            raise ValueError(f"Unexpected response: {content}")

def get_food_smalltalk_answer(prompt):
    system_message = (
        "Ты отвечаешь как опытный диетолог. На вопросы по питанию, еде, спорту или диете давай короткие и полезные ответы. "
        "Если вопрос не связан с этими темами, сообщи, что пока не можешь на него ответить."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )

    answer_string = response.choices[0].message.content
    logger.info(f'function get_food_smalltalk_answer answer from API {answer_string=}')
    return answer_string
