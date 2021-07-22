""" Base model class which allows for persistence """
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel
from pymongo.database import Database
from pymongo.collection import Collection


# pylint: disable=missing-class-docstring


class BaseDBModel(BaseModel, ABC):
    db: Database
    _exclude = {'db'}

    class Config:
        arbitrary_types_allowed = True

    def dict(self, **kwargs):
        return super().dict(exclude=self.exclude_attrs, **kwargs)

    def save(self):
        """ Saves the record to the DB (update if it exists) """
        self.collection.update_one(
            filter=self.unique_key,
            update={"$set": self.dict()},
            upsert=True
        )

    @property
    @abstractmethod
    def collection(self) -> Collection:
        pass

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
    db: Database

    def __init__(self, db: Database):
        self.db = db

    def find_one(self, key: dict) -> dict:
        return self.collection.find_one(key)

    def find_many(self, criteria: dict = None):
        return self.collection.find(filter=criteria)

    @property
    @abstractmethod
    def collection(self) -> Collection:
        pass

