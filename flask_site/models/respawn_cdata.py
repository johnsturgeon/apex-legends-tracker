""" Dataclass to represent respawn c_data collection """
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache, cached_property
from typing import List

# pylint: disable=import-error
from pydantic import BaseModel

from models.base_db_model import BaseDBModel, BaseDBCollection
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))


# pylint: disable=missing-class-docstring
class CDataException(Exception):
    pass


class CDataLegendNotFound(Exception):
    pass


class CDataCategory(str, Enum):
    BADGE = "badge"
    CHARACTER = "character"
    CHARACTER_FRAME = "character_frame"
    CHARACTER_SKIN = "character_skin"
    CHARACTER_STANCE = "character_stance"
    INTRO_QUIP = "intro_quip"
    TRACKER = "tracker"


class CDataTrackerGrouping(str, Enum):
    DAMAGE = "damage"
    EXECUTIONS = "executions"
    GAMES_PLAYED = "games_played"
    HEADSHOTS = "headshots"
    KILLS = "kills"
    REVIVES = "revives"
    TOP_3 = "top_3"
    UNGROUPED = "ungrouped"
    WINS = "wins"


class CDataTrackerMode(str, Enum):
    ARENAS = "arenas"
    BATTLE_ROYALE = "battle_royale"


class CData(BaseDBModel):
    c_data: int
    name: str
    key: str
    legend: str
    category: CDataCategory

    @property
    def unique_key(self) -> dict:
        return {'c_data': self.c_data}


class CDataTracker(CData):
    tracker_grouping: CDataTrackerGrouping
    tracker_mode: CDataTrackerMode


class CDataTrackerValue(BaseModel):
    cdata_tracker: CDataTracker
    value: int


class CDataCollection(BaseDBCollection):
    """
    This is a collection class.  It's primary objective is to abstract the DB interface so that
    the caller can just ask for objects from the CData MongoDB collection without knowing they're
    dealing with a database.
    """
    def obj_from_record(self, record: dict):
        return CData(
            db_collection=self.db_collection,
            **record
        )

    @cached_property
    def all_records(self) -> dict:
        """ Returns a cached dict of all c_data records """
        cached_records: dict = {}
        for record in self.db_collection.find():
            cached_records[record['c_data']] = record
        return cached_records

    @lru_cache
    def retrieve_one_record(self, c_data: int, category: CDataCategory = None) -> dict:
        """ Guaranteed to return one record """
        record = self.all_records.get(c_data)
        if not record:
            raise CDataException(f"Record not found for c_data: {c_data}")
        if category and record['category'] != category.value:
            raise CDataException(
                f"Record found, but wrong category: {category.value} (for c_data: {c_data})"
            )
        return record

    @lru_cache
    def retrieve_many(self) -> List[CData]:
        """ Fetch records from the db, and return them as model objects """
        retrieved_records: List[CData] = []
        record_list = list(self.all_records.values())
        for record in record_list:
            retrieved_records.append(self.obj_from_record(record))
        return retrieved_records

    # pylint: disable=missing-function-docstring
    @lru_cache
    def retrieve_one(self, c_data: int) -> CData:
        return self.obj_from_record(self.retrieve_one_record(c_data))

    @lru_cache
    def retrieve_legend(self, c_data: int) -> CData:
        return self.obj_from_record(self.retrieve_one_record(c_data, CDataCategory.CHARACTER))

    @cached_property
    def tracker_collection(self) -> CDataTrackerCollection:
        return CDataTrackerCollection(db_collection=self.db_collection)


class CDataTrackerCollection(CDataCollection):

    def obj_from_record(self, record: dict):
        return CDataTracker(db_collection=self.db_collection, **record)

    @lru_cache
    def retrieve_one(self, c_data: int) -> CDataTracker:
        return self.obj_from_record(self.retrieve_one_record(c_data, CDataCategory.TRACKER))


def try_cdata_test():
    """ Utility function"""
    # pylint: disable=import-outside-toplevel
    from apex_db_helper import ApexDBHelper

    collection: CDataCollection = CDataCollection(ApexDBHelper().database.respawn_cdata)
    record: CData
    for record in collection.retrieve_many():
        print(record)
    print(len(collection.retrieve_many()))


if __name__ == '__main__':
    try_cdata_test()
