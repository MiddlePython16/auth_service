import time
from functools import wraps
from typing import Optional, Callable


def backoff(exceptions: tuple, start_sleep_time=0.1, factor=2, border_sleep_time=10,
            callback: Optional[Callable] = None, default=...):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка.
    Использует наивный экспоненциальный рост времени повтора (factor)
    до граничного времени ожидания (border_sleep_time)
    Формула:
        t = start_sleep_time * n if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :param exceptions: список экспешенов, которые отвечают за ошибку
    :param callback: вызываемый объект, на вход передаётся ошибка
    :param default: если передан, то по окончанию времени на попытки это
                    значение будет возвращено вместо результата функции
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            t = start_sleep_time
            while t < border_sleep_time:
                t = t * factor
                t = t if t < border_sleep_time else border_sleep_time
                time.sleep(t)
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if callback:
                        callback(e)
            if default is ...:
                raise ConnectionError
            return default

        return inner

    return func_wrapper
