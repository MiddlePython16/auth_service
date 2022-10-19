import glob
import importlib
import os
import re
import secrets
import string
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from os.path import join
from time import sleep

from flask import Flask, Response, current_app, json, request
from flask_jwt_extended import (current_user, get_csrf_token,
                                get_jwt_request_location)
from flask_restx import Api
from models.models import MethodEnum, User
from services.logs_service import get_logs_service

PASSWORD_LEN = 20


def save_activity(user: User, action=None):
    device = f'{request.user_agent}'
    method = getattr(MethodEnum, request.method.lower())
    log_service = get_logs_service()

    log_service.create_log(
        user_id=user.id,
        when=datetime.now(),
        action=action,
        device=device,
        method=method,
    )


def register_blueprints(app: Flask):
    modules = glob.glob(join('views', '*.py'))
    modules = list(map(lambda module: module.replace('/', '.'), modules))  # noqa: C417
    for module_name in modules:
        if not module_name.endswith('__init__.py'):
            name = module_name.split('.')[1]
            module_name = importlib.import_module(module_name[:-3])
            app.register_blueprint(getattr(module_name, f'{name}_view'))


def register_namespaces(api: Api):  # noqa: WPS210
    for path in os.walk('api'):
        for module_name in path[2]:
            path_to_module = f'{path[0]}/{module_name}'
            module_path_without_extension = path_to_module.replace('/', '.')[:-3]
            if not re.search('__.*__.py', module_name) and re.search('py$', module_name):
                module = importlib.import_module(module_path_without_extension)
                namespace = getattr(module, module_name[:-3])
                api.add_namespace(namespace)


def handle_csrf():
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if current_user and get_jwt_request_location() == 'cookies':
                token = request.cookies['csrf_access_token']
                request.headers['X-CSRF-TOKEN'] = get_csrf_token(encoded_token=token)
            return func(*args, **kwargs)

        return inner

    return func_wrapper


def work_in_context(app):
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)

        return inner

    return func_wrapper


def log_activity(action=None):
    def func_wrapper(func):
        @wraps(func)
        @work_in_context(current_app)
        def inner(*args, **kwargs):
            function_result = func(*args, **kwargs)
            if not current_user:
                return function_result
            save_activity(current_user, action=action)
            return function_result

        return inner

    return func_wrapper


def required_role_level(level: int):
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if any(role.level >= level for role in current_user.roles):
                return func(*args, **kwargs)
            return make_error_response(
                msg='Role level is not enough',
                status=HTTPStatus.FORBIDDEN,
            )

        return inner

    return func_wrapper


def make_error_response(msg: str, status: int) -> Response:
    return Response(
        response=json.dumps({'msg': msg}),
        status=status,
        content_type='application/json',
    )


def generate_password():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(PASSWORD_LEN))


def backoff(exceptions: tuple, start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка.
    Использует наивный экспоненциальный рост времени повтора (factor)
    до граничного времени ожидания (border_sleep_time)
    Формула:
        t = start_sleep_time * 2^(n) if t < border_sleep_time
        t = border_sleep_time if t >= border_sleep_time
    :param start_sleep_time: начальное время повтора
    :param factor: во сколько раз нужно увеличить время ожидания
    :param border_sleep_time: граничное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            t = start_sleep_time
            while t < border_sleep_time:
                t = t * factor
                t = t if t < border_sleep_time else border_sleep_time
                sleep(t)
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    pass
            raise ConnectionError

        return inner

    return
