""" Base model class which allows for persistence """
from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field
from pymongo.collection import Collection


# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
class BaseDBModel(BaseModel, ABC):
    db_collection: Collection = Field(exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def save(self):
        """ Saves the record to the DB (update if it exists) """
        # pylint: disable=no-member
        self.db_collection.update_one(
            filter=self.unique_key,
            update={"$set": self.dict()},
            upsert=True
        )

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
