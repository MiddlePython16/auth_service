from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Optional

from extensions.tracer import trace_decorator
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query


class AdditionalActions(str, Enum):
    sort_by = '_sort_by'
    first = '_first'


def get_actions_dict(**kwargs) -> tuple[dict, dict]:
    actions = {}
    for action in AdditionalActions:
        if action.value in kwargs and action.value:
            actions[action.value] = kwargs.pop(action.value)
        else:
            actions[action.value] = None
    return actions, kwargs


def sqlalchemy_additional_actions():
    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            actions, kwargs = get_actions_dict(**kwargs)
            query: Query = func(*args, **kwargs)
            model = kwargs['model']

            # Сортировка
            sort_value = actions[AdditionalActions.sort_by]
            if sort_value:
                if sort_value.startswith('-'):
                    query.order_by(getattr(model, sort_value).desc())
                else:
                    query.order_by(getattr(model, sort_value))

            # Если необходимо получить один элемент
            if actions[AdditionalActions.first]:
                query = query.first()
            return query

        return inner

    return func_wrapper


class MainStorage(ABC):  # noqa: WPS214
    @abstractmethod
    def get(self, item_id: str, model, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def create(self, model, need_commit: bool = True, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def update(self, item_id: str, model, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def commit(self, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def add(self, *args, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def delete(self, item_id: str, model, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def get_all(self, **kwargs):  # noqa: WPS463
        pass  # noqa: WPS420

    @abstractmethod
    def filter_by(self, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def filter(self, *args, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def paginate(self, query: Query, page: int, per_page: int, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def count(self, query: Query, **kwargs):
        pass  # noqa: WPS420

    @abstractmethod
    def like(self, model, query: Query, field, pattern: str, **kwargs):  # noqa: WPS211
        pass  # noqa: WPS420

    @abstractmethod
    def get_query(self, model, *args, **kwargs):  # noqa: WPS463
        pass  # noqa: WPS420


class BaseSQLAlchemyStorage(MainStorage):  # noqa: WPS214
    def __init__(self, db: SQLAlchemy):
        self.db = db

    def get(self, item_id: str, model, **kwargs):
        return model.query.get(item_id)

    def create(self, model, need_commit: bool = True, **kwargs):
        entity = model(**kwargs)
        self.add(entity)

        if need_commit:
            self.commit()
        return entity

    def update(self, item_id: str, model, **kwargs):
        model.query.filter_by(id=item_id).update(kwargs)
        self.commit()

    @sqlalchemy_additional_actions()
    def filter_by(self, model, query: Optional[Query] = None, **kwargs):
        if query:
            return query.filter_by(**kwargs)
        return model.query.filter_by(**kwargs)

    @sqlalchemy_additional_actions()
    def filter(self, model, query: Optional[Query] = None, *args, **kwargs):
        if query:
            return query.filter(*args, **kwargs)
        return model.query.filter(*args, **kwargs)

    def commit(self, **kwargs):
        return self.db.session.commit(**kwargs)

    def add(self, *args, **kwargs):
        return self.db.session.add(*args)

    def delete(self, item_id: str, model, **kwargs):
        model.query.filter_by(id=item_id).delete()
        self.commit()

    def get_all(self, model, **kwargs):
        return model.query.all()

    def paginate(self, query: Query, page: int, per_page: int, **kwargs):
        return query.paginate(page, per_page, error_out=False)

    def count(self, query: Query, **kwargs):
        return query.count()

    def like(self, model, query: Query, field, pattern: str, **kwargs):  # noqa: WPS211
        model_field = getattr(model, field)
        return query.filter(model_field.like(pattern))

    def get_query(self, model, *args, **kwargs):
        return model.query


class BaseMainStorage:  # noqa: WPS214
    def __init__(self, db: BaseSQLAlchemyStorage, db_model, **kwargs):
        super().__init__(**kwargs)

        self.db = db
        self.model = db_model

    @trace_decorator()
    def get(self, item_id: str):
        return self.db.get(item_id=item_id, model=self.model)

    @trace_decorator()
    def delete(self, item_id: str):
        return self.db.delete(item_id=item_id, model=self.model)

    @trace_decorator()
    def filter_by(self, _first=None, _sort_by=None, **kwargs):
        return self.db.filter_by(model=self.model, _first=_first, **kwargs)

    @trace_decorator()
    def filter(self, _first=None, _sort_by=None, *args, **kwargs):
        return self.db.filter(model=self.model, _first=_first, *args, **kwargs)

    @trace_decorator()
    def create(self, **kwargs):
        return self.db.create(model=self.model, **kwargs)

    @trace_decorator()
    def update(self, item_id: str, **kwargs):
        return self.db.update(item_id=item_id, model=self.model, **kwargs)

    @trace_decorator()
    def get_all(self, **kwargs):
        return self.db.get_all(model=self.model, **kwargs)

    @trace_decorator()
    def paginate(self, query, page: int, per_page: int, **kwargs):
        return self.db.paginate(query=query, page=page, per_page=per_page, **kwargs)

    @trace_decorator()
    def count(self, query, **kwargs) -> int:
        return self.db.count(query, **kwargs)

    @trace_decorator()
    def like(self, query, field, pattern: str, **kwargs):
        return self.db.like(
            query=query,
            model=self.model,
            field=field,
            pattern=pattern,
            **kwargs,
        )

    @trace_decorator()
    def get_query(self, **kwargs):
        return self.db.get_query(model=self.model, **kwargs)
