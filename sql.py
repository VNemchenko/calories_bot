from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, select, func, inspect, DateTime, Date
from datetime import datetime
from config import HOST, DATABASE, DB_USER, DB_PASSWORD, logger


engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{HOST}:5432/{DATABASE}')
metadata = MetaData()


def create_users_table():
    insp = inspect(engine)
    if not insp.has_table("users"):
        users_table = Table('users', metadata,
                            Column('user_id', Integer, primary_key=True),
                            Column('start_date', DateTime),
                            Column('last_payment_date', DateTime))
        users_table.create(engine)
        logger.info(f'function create_users_table started with new table')
    else:
        users_table = Table('users', metadata, autoload_with=engine)
        logger.info(f'function create_users_table started with exist table')
    return users_table

def get_user(users_table, user_id):
    logger.info(f'function get_user started')
    with engine.connect() as connection:
        query = select().select_from(users_table).where(users_table.c.user_id == user_id)
        result = connection.execute(query).fetchone()
        return result

def add_user(users_table, user_id):
    logger.info(f'function add_user started')
    with engine.connect() as connection:
        date = datetime.now()  # теперь date - это объект datetime, а не строка
        connection.execute(users_table.insert().values(user_id=user_id, start_date=date, last_payment_date=date))

def update_payment_date(users_table, user_id):
    logger.info(f'function update_payment_date started')
    with engine.connect() as connection:
        date = datetime.now()  # теперь date - это объект datetime, а не строка
        connection.execute(users_table.update().where(users_table.c.user_id == user_id).values(last_payment_date=date))


def create_nutrition_table():
    insp = inspect(engine)
    if not insp.has_table("nutrition"):
        nutrition_table = Table('nutrition', metadata,
                                Column('date', Date, primary_key=True),
                                Column('user_id', Integer, primary_key=True),
                                Column('fat', Integer),
                                Column('protein', Integer),
                                Column('carbs', Integer),
                                Column('calories', Integer),
                                Column('text', String))
        nutrition_table.create(engine)
        logger.info(f'function create_nutrition_table started with new table')
    else:
        nutrition_table = Table('nutrition', metadata, autoload_with=engine)
        logger.info(f'function create_nutrition_table started with exist table')
    return nutrition_table


def add_test_entry(nutrition_table):
    with engine.connect() as connection:
        date = datetime.now().date()  # используем только дату, без времени
        connection.execute(
            nutrition_table.insert().values(
                date=date,
                user_id=1,
                fat=10,
                protein=20,
                carbs=30,
                calories=40,
                text='test entry')
        )


def add_entry(nutrition_table, user_id, json_data):
    add_test_entry(nutrition_table)
    with engine.connect() as connection:
        date = datetime.now().date()  # теперь date - это объект date, а не строка
        logger.info(f'function add_entry received data {json_data=}')
        query = select().select_from(nutrition_table).where(nutrition_table.c.date == date, nutrition_table.c.user_id == user_id)
        result = connection.execute(query).fetchone()

        if result:
            # Обновляем существующую запись
            logger.info(f'function add_entry started with exist record')
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
            logger.info(f'function add_entry started with new record')
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


def get_data_from_db(nutrition_table, user_id, date_str):
    logger.info(f'function get_data_from_db started')
    with engine.connect() as connection:
        try:
            # Парсим дату из строки
            date_obj = datetime.strptime(date_str, "%d.%m.%y").date()
            logger.info(f'function get_data_from_db started with {date_obj=}')

            query = select().select_from(nutrition_table).where(nutrition_table.c.date == date_obj,
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
                return "Нет данных для этой даты."

        except ValueError:
            return "Ошибка: дата должна быть в формате DD.MM.YY."
