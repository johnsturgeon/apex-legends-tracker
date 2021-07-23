""" Base model class which allows for persistence """
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel
from pymongo.database import Database
from pymongo.collection import Collection


# pylint: disable=missing-class-docstring


class BaseDBModel(BaseModel, ABC):
    db_collection: Collection
    _exclude = {'db_collection'}

    class Config:
        arbitrary_types_allowed = True

    def dict(self, **kwargs):
        del kwargs['exclude']
        return super().dict(exclude=self.exclude_attrs, **kwargs)

    def save(self):
        """ Saves the record to the DB (update if it exists) """
        self.db_collection.update_one(
            filter=self.unique_key,
            update={"$set": self.dict()},
            upsert=True
        )

    @property
    def exclude_attrs(self) -> set:
        res = set()
        for cls in type(self).mro():
            res |= getattr(cls, '_exclude', set())
        return res

    @property
    @abstractmethod
    def unique_key(self) -> dict:
        pass


class BaseDBCollection(ABC):

    def __init__(self, db_collection: Collection):
        self.db_collection = db_collection

    def find_one(self, key: dict) -> dict:
        return self.db_collection.find_one(key)

    def find_many(self, criteria: dict = None):
        return self.db_collection.find(filter=criteria)

    @abstractmethod
    def obj_from_record(self, record: dict):
        pass

