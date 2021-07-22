""" Dataclass to represent respawn c_data collection """
from __future__ import annotations

import os
from enum import Enum
from typing import List

from pymongo.collection import Collection
from pymongo.database import Database

# pylint: disable=import-error
from base_db_model import BaseDBModel, BaseDBCollection
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))


class CDataException(Exception):
    pass


class CDataLegendNotFound(Exception):
    pass


# pylint: disable=missing-class-docstring
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
    value: str
    key: str
    category: CDataCategory

    @property
    def unique_key(self) -> dict:
        return {'c_data': self.c_data}

    @property
    def collection(self) -> Collection:
        return self.db.respawn_cdata


class CDataTracker(CData):
    tracker_grouping: CDataTrackerGrouping
    tracker_mode: CDataTrackerMode


class CDataCollection(BaseDBCollection):

    def __init__(self, db: Database):
        super().__init__(db)
        self._cached_records: dict = dict()
        for record in self.collection.find():
            self._cached_records[record['c_data']] = record

    def retrieve_one_record(self, c_data: int, category: CDataCategory = None) -> dict:
        """ Guaranteed to return one record """
        record = self._cached_records.get(c_data)
        if not record:
            raise CDataException("Record not found for c_data: %s", c_data)
        if category and record['category'] != category.value:
            raise CDataException(
                "Record found, but wrong category: %s (for c_data: %s)", category.value, c_data
            )
        return record

    def retrieve_many(self, criteria: dict = None) -> List[CData]:
        retrieved_records: List[CData] = list()
        if criteria is None:
            record_list = list(self._cached_records.values())
        else:
            record_list = list(self.find_many(criteria))
        for record in record_list:
            retrieved_records.append(CData(db=self.db, **record))
        return retrieved_records

    def retrieve_tracker(self, c_data: int) -> CDataTracker:
        record = self.retrieve_one_record(c_data, CDataCategory.TRACKER)
        return CDataTracker(db=self.db, **record)

    def retrieve_cdata(self, c_data: int) -> CData:
        record = self.retrieve_one_record(c_data)
        return CData(db=self.db, **record)

    def retrieve_legend(self, c_data: int) -> CData:
        record = self.retrieve_one_record(c_data, CDataCategory.CHARACTER)
        return CData(db=self.db, **record)

    @property
    def collection(self) -> Collection:
        return self.db.respawn_cdata


def try_cdata_test():
    from apex_db_helper import ApexDBHelper

    collection: CDataCollection = CDataCollection(ApexDBHelper().database)
    record: CData
    for record in collection.retrieve_many():
        print(record)
    print(len(collection.retrieve_many()))


if __name__ == '__main__':
    try_cdata_test()
