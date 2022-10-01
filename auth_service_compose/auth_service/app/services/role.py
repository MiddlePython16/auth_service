import uuid  # noqa: E999
from functools import lru_cache

from db.cache_db import get_cache_db
from db.db import get_db
from extensions.tracer import trace_decorator
from models import models
from pydantic import BaseModel, Field
from pydantic.types import UUID4
from services.base_cache import BaseCacheStorage
from services.base_main import BaseMainStorage


class CacheRole(BaseModel):
    id: UUID4 = Field(default_factory=uuid.uuid4)
    name: str
    level: int


class RoleService(BaseCacheStorage, BaseMainStorage):
    cache_model = CacheRole

    @trace_decorator()
    def get_roles(
            self,
            page: int,
            per_page: int,
            base_url: str,
    ):
        query = self.get_query()

        cache_key = f'{base_url}?page={page}&per_page={per_page}'
        roles = self.get_items_from_cache(cache_key=cache_key, model=self.cache_model)
        if not roles:
            paginated_roles = self.paginate(query=query, page=page, per_page=per_page)
            roles = [self.cache_model(**role.to_dict()) for role in paginated_roles.items]
            if roles:
                self.put_items_to_cache(cache_key=cache_key, entities=roles)

        return {
            'items': roles,
            'total': self.count(query),
            'page': page,
            'per_page': per_page,
        }

    @trace_decorator()
    def get_role(self, role_id: str, base_url: str):
        cache_key = base_url
        role = self.get_one_item_from_cache(cache_key=cache_key, model=self.cache_model)
        if not role:
            db_role = self.get(item_id=role_id)
            if db_role:
                role = self.cache_model(**db_role.to_dict())
                self.put_one_item_to_cache(cache_key=cache_key, entity=role)
        return role

    @trace_decorator()
    def update_role(self, role_id: str, role_params: dict):
        self.update(item_id=role_id, **role_params)

    @trace_decorator()
    def create_role(self, role_params: dict):
        role = self.create(**role_params)
        return self.cache_model(**role.to_dict())


@lru_cache()
def get_role_service() -> RoleService:
    return RoleService(
        cache=get_cache_db(),
        db=get_db(),
        db_model=models.Role,
    )
