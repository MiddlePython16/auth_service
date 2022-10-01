from flask_restx import reqparse
from pydantic import BaseModel

DEFAULT_PAGE_SIZE = 20

pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, location='args', default=1)
pagination_parser.add_argument('per_page', type=int, location='args', default=DEFAULT_PAGE_SIZE)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list  # noqa: WPS110

    def prepare_items_for_answer(self, model):
        self.items = [model(**entity.dict()).dict()  # noqa: WPS110
                      for entity in self.items]
