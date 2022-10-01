from abc import ABC, abstractmethod

from extensions.tracer import trace_decorator
from kafka import KafkaProducer


class AbstractProducer(ABC):
    @abstractmethod
    def send(self, topic: str, message: bytes, key: bytes):
        pass  # noqa: WPS420


class BaseKafkaProducer(AbstractProducer):
    def __init__(self, db_producer: KafkaProducer):
        self.db_producer = db_producer

    def send(self, topic: str, message: bytes, key: bytes):
        self.db_producer.send(topic=topic, value=message, key=key)


class MainProducer:
    def __init__(self, db: BaseKafkaProducer):
        self.db = db

    @trace_decorator()
    def send(self, topic: str, message: bytes, key: bytes):
        return self.db.send(topic=topic, message=message, key=key)
