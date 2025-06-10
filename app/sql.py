from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, desc, func, select, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from config import HOST, DATABASE, DB_USER, DB_PASSWORD, logger, datetime

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{HOST}:5432/{DATABASE}', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)  # новое поле
    start_date = Column(DateTime)
    last_payment_date = Column(DateTime)
    request_count = Column(Integer, default=0)
    is_vip = Column(Boolean, default=False)
    timezone = Column(String, default='UTC')
    last_reminder_date = Column(Date)

class Nutrition(Base):
    __tablename__ = 'nutrition'
    date = Column(Date, primary_key=True)
    user_id = Column(Integer, primary_key=True)
    fat = Column(Integer)
    protein = Column(Integer)
    carbs = Column(Integer)
    calories = Column(Integer)
    text = Column(String)

Base.metadata.create_all(engine)

def reset_block_and_counter():
    with Session() as session:
        users = session.query(User).all()
        for user in users:
            user.request_count = 0
        session.commit()


def increment_request_counter(user_id):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.request_count += 1
            session.commit()


def is_user_vip(user_id):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user and ((datetime.now() - user.last_payment_date).days <= 7 or user.is_vip):
            return True
        else:
            return False


def make_user_vip(user_id):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.is_vip = True
            session.commit()


def requests_count(user_id):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        return user.request_count if user else 0


def get_user_position(user_id):
    logger.info(f'function get_user_position started')
    date = datetime.now().date()
    with Session() as session:
        # Создаём подзапрос с ранжированием пользователей по калорийности
        stmt = select([
            Nutrition.user_id,
            func.rank().over(order_by=desc(Nutrition.calories)).label('rank_from_bottom'),
            func.rank().over(order_by=Nutrition.calories).label('rank_from_top')
        ]).where(Nutrition.date == date).subquery()

        # Запрашиваем ранжирование для конкретного пользователя
        user_rank = session.query(stmt).filter(stmt.c.user_id == user_id).first()

        # Получаем общее количество пользователей за день
        total_users = session.query(Nutrition).filter(Nutrition.date == date).count()

        if user_rank is None:
            return f"Вы еще не вносили записи сегодня."
        else:
            return f"Сегодня вы на {user_rank.rank_from_top} месте по калориям, " \
                   f"и на {user_rank.rank_from_bottom} месте по дефициту. Всего участвуют {total_users} пользователей."


def get_user(user_id, chat_id):
    logger.info(f'function get_user started')
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user and user.chat_id != chat_id:  # проверяем, отличается ли chat_id
            user.chat_id = chat_id  # если отличается, обновляем его
            session.commit()  # сохраняем изменения
    return user


def add_user(user_id, chat_id):  # добавляем chat_id как аргумент
    logger.info(f'function add_user started. Type of user is {type(user_id)}')
    with Session() as session:
        date = datetime.now()
        new_user = User(user_id=user_id, chat_id=chat_id, start_date=date, last_payment_date=date)
        session.add(new_user)
        session.commit()


def get_chat_ids() -> list:
    with Session() as session:
        chat_ids = session.query(User.chat_id).distinct()  # получаем все уникальные chat_id
        # преобразуем результат в список для удобства
        chat_ids = [chat_id[0] for chat_id in chat_ids]
    return chat_ids


def update_user_timezone(user_id, timezone: str):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.timezone = timezone
            session.commit()


def get_all_users():
    with Session() as session:
        return session.query(User).all()


def has_entry_for_date(user_id, date):
    with Session() as session:
        return session.query(Nutrition).filter(
            Nutrition.user_id == user_id,
            Nutrition.date == date
        ).count() > 0


def update_payment_date(user_id):
    logger.info(f'function update_payment_date started')
    with Session() as session:
        date = datetime.now()
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.last_payment_date = date
            session.commit()


def add_entry(user_id, json_data, date):
    with Session() as session:
        logger.info(f'function add_entry received data {json_data=}')
        nutrition = session.query(Nutrition).filter(Nutrition.date == date, Nutrition.user_id == user_id).first()

        if nutrition:
            logger.info(f'function add_entry started with exist record')
            nutrition.fat += json_data['fat']
            nutrition.protein += json_data['protein']
            nutrition.carbs += json_data['carbs']
            nutrition.calories += json_data['calories']
            nutrition.text += ', ' + json_data['text']
        else:
            logger.info(f'function add_entry started with new record')
            new_nutrition = Nutrition(date=date, user_id=user_id, fat=json_data['fat'],
                                      protein=json_data['protein'], carbs=json_data['carbs'],
                                      calories=json_data['calories'], text=json_data['text'])
            session.add(new_nutrition)

        session.commit()
    increment_request_counter(user_id)

    return f"Записано на {date}. Это примерно {json_data['fat']} гр. жиров, {json_data['protein']} гр. белков и {json_data['carbs']} гр. углеводов, всего {json_data['calories']} Ккал."


def get_data_from_db(user_id, date):
    logger.info(f'function get_data_from_db started')
    with Session() as session:
        logger.info(f'function get_data_from_db started with {date=}')

        nutrition = session.query(Nutrition).filter(Nutrition.date == date,
                                                    Nutrition.user_id == user_id).first()

        if nutrition:
            return f"Дата: {nutrition.date}\n" \
                   f"Жиры: {nutrition.fat} гр.\n" \
                   f"Белки: {nutrition.protein} гр.\n" \
                   f"Углеводы: {nutrition.carbs} гр.\n" \
                   f"Калории: {nutrition.calories} Ккал.\n" \
                   f"({nutrition.text})"
        else:
            return "Нет данных для этой даты."
