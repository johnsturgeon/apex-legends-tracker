""" Base model class which allows for persistence """
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Callable, TypeVar, NewType
from uuid import UUID

from pydantic import BaseModel
from pymongo.collection import Collection


# pylint: disable=missing-class-docstring
class BaseDBModel(BaseModel, ABC):
    collection: Collection
    uuid: UUID
    _exclude_attrs: set = {'collection'}

    class Config:
        arbitrary_types_allowed = True

    def dict(self, **kwargs):
        return super().dict(exclude=self._exclude_attrs, **kwargs)

    def save(self):
        """ Saves the record to the DB (update if it exists) """
        self.collection.update_one(
            filter={'uuid': self.uuid},
            update={"$set": self.dict()},
            upsert=True
        )


class BaseDBCollection(ABC):

    def __init__(self, collection: Collection):
        self.collection = collection
        super().__init__()

    def _find_one(self, uuid: UUID) -> dict:
        return self.collection.find_one({'uuid': uuid})

    def _find_many(self, criteria: dict = None):
        return self.collection.find(filter=criteria)

    @abstractmethod
    def retrieve_one(self, uuid: UUID):
        pass

    @abstractmethod
    def retrieve_all(self, criteria: dict = None):
        pass
