from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from kafka import KafkaProducer
from kafka.errors import KafkaError

from core.settings import settings
from services.base_main import BaseSQLAlchemyStorage, MainStorage
from services.notify_pipeline import BaseKafkaProducer, MainProducer
from utils.backoff import backoff
from utils.exceptions import CantGetInitializedObjectError

db: Optional[MainStorage] = None
sqlalchemy = SQLAlchemy()
notify_pipeline: Optional[MainProducer] = None


def init_sqlalchemy(app: Flask, storage: BaseSQLAlchemyStorage):
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}?options=-c%20search_path=content'  # noqa: E501, WPS221, WPS323
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

    storage.db.init_app(app)


@backoff(exceptions=(KafkaError,),
         factor=10,
         callback=lambda x: print(f'kafka fucked up {x}', flush=True),
         default=None)
def init_pipeline() -> MainProducer:
    producer = KafkaProducer(
        bootstrap_servers=[f'{settings.KAFKA_HOST}:{settings.KAFKA_PORT}'],
        api_version=(0, 11, 5),
    )
    if producer.bootstrap_connected():
        return MainProducer(db=BaseKafkaProducer(
            db_producer=producer,
        ))
    raise KafkaError


def get_db() -> MainStorage:
    if not db:
        raise CantGetInitializedObjectError(object_name='main db')
    return db


def get_notify_pipeline() -> Optional[MainProducer]:
    if not notify_pipeline:
        return None
    return notify_pipeline
