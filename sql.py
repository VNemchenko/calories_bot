from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, select, func
from datetime import datetime
from config import HOST, DATABASE, DB_USER, DB_PASSWORD

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{HOST}:5432/{DATABASE}')
metadata = MetaData()

# Определение структуры таблицы
nutrition_table = Table('nutrition', metadata, autoload_with=engine)
users_table = Table('users', metadata, autoload_with=engine)


# def create_users_table():
#     if not engine.dialect.has_table(engine, "users"):
#         users = Table('users', metadata,
#                       Column('user_id', String, primary_key=True),
#                       Column('start_date', String),
#                       Column('last_payment_date', String))
#         users.create(engine)

def get_user(user_id):
    with engine.connect() as connection:
        query = select([users_table]).where(users_table.c.user_id == user_id)
        result = connection.execute(query).fetchone()
        return result

def add_user(user_id):
    with engine.connect() as connection:
        date = datetime.now().strftime('%d-%m-%Y')
        connection.execute(users_table.insert().values(user_id=user_id, start_date=date, last_payment_date=date))

def update_payment_date(user_id):
    with engine.connect() as connection:
        date = datetime.now().strftime('%d-%m-%Y')
        connection.execute(users_table.update().where(users_table.c.user_id == user_id).values(last_payment_date=date))


# def create_table():
#     if not engine.dialect.has_table(engine, "nutrition"):
#         nutrition = Table('nutrition', metadata,
#                           Column('date', String, primary_key=True),
#                           Column('user_id', String, primary_key=True),
#                           Column('fat', Integer),
#                           Column('protein', Integer),
#                           Column('carbs', Integer),
#                           Column('calories', Integer),
#                           Column('text', String))
#         nutrition.create(engine)


def add_entry(user_id, json_data):
    with engine.connect() as connection:
        date = datetime.now().strftime('%d-%m-%Y')  # форматируем текущую дату в строку dd-mm-yyyy
        query = select([nutrition_table]).where(nutrition_table.c.date == date, nutrition_table.c.user_id == user_id)
        result = connection.execute(query).fetchone()

        if result:
            # Обновляем существующую запись
            connection.execute(
                nutrition_table.update().where(nutrition_table.c.date == date,
                                               nutrition_table.c.user_id == user_id).values(
                    fat=nutrition_table.c.fat + json_data['fat'],
                    protein=nutrition_table.c.protein + json_data['protein'],
                    carbs=nutrition_table.c.carbs + json_data['carbs'],
                    calories=nutrition_table.c.calories + json_data['calories'],
                    text=nutrition_table.c.text + ', ' + json_data['text'])
            )
        else:
            # Добавляем новую запись
            connection.execute(
                nutrition_table.insert().values(
                    date=date,
                    user_id=user_id,
                    fat=json_data['fat'],
                    protein=json_data['protein'],
                    carbs=json_data['carbs'],
                    calories=json_data['calories'],
                    text=json_data['text'])
            )

        return f"Принял и запомнил. Это примерно {json_data['fat']} гр. жиров, {json_data['protein']} гр. белков и {json_data['carbs']} гр. углеводов, всего {json_data['calories']} ккал"


def get_data_from_db(user_id, date_str):
    with engine.connect() as connection:
        try:
            # Парсим дату из строки
            date_obj = datetime.strptime(date_str, "%d.%m.%y")
            date_db_format = date_obj.strftime('%d-%m-%Y')  # Преобразуем дату в формат, используемый в БД

            query = select([nutrition_table]).where(nutrition_table.c.date == date_db_format,
                                                    nutrition_table.c.user_id == user_id)
            result = connection.execute(query).fetchone()

            if result:
                # Возвращаем данные в виде текста
                return f"Дата: {result['date']}\n" \
                       f"Жиры: {result['fat']}\n" \
                       f"Белки: {result['protein']}\n" \
                       f"Углеводы: {result['carbs']}\n" \
                       f"Калории: {result['calories']}\n" \
                       f"({result['text']})"
            else:
                return "Нет данных для данной даты."

        except ValueError:
            return "Ошибка: дата должна быть в формате DD.MM.YY."
