import time
from functools import wraps


def retry(exception_to_check, tries=3, delay=2, backoff=2):
    """Декоратор повторяющий вызов функции в случае исключения
    exception_to_check: исключение или кортеж исключений, для которых нужно повторять вызов функции
    tries: максимальное количество попыток
    delay: начальное время ожидания между попытками
    backoff: множитель, на который увеличивается время ожидания
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    if mtries == 1:  # это последняя попытка
                        raise  # поднимаем исключение
                    else:
                        print(f"{str(e)}, Retrying in {mdelay} seconds...")
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff

        return f_retry  # true decorator
    return deco_retry
