""" Dataclass to represent respawn c_data collection """
from __future__ import annotations

import os
from enum import Enum
from typing import List
from uuid import uuid4, UUID

from pymongo.collection import Collection

# pylint: disable=import-error
from base_db_model import BaseDBModel, BaseDBCollection
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))


# pylint: disable=missing-class-docstring
class CDataLegend(str, Enum):
    ALL = "all"
    BANGALORE = "Bangalore"
    BLOODHOUND = "Bloodhound"
    CAUSTIC = "Caustic"
    CRYPTO = "Crypto"
    FUSE = "Fuse"
    GIBRALTAR = "Gibraltar"
    HORIZON = "Horizon"
    LIFELINE = "Lifeline"
    LOBA = "Loba"
    MIRAGE = "Mirage"
    OCTANE = "Octane"
    PATHFINDER = "Pathfinder"
    RAMPART = "Rampart"
    REVENANT = "Revenant"
    VALKYRIE = "Valkyrie"
    WATTSON = "Wattson"
    WRAITH = "Wraith"


class CDataCategory(str, Enum):
    BADGE = "badge"
    CHARACTER_FRAME = "character_frame"
    CHARACTER_SKIN = "character_skin"
    INTRO_QUIP = "intro_quip"
    TRACKER = "tracker"


class CDataTrackerGrouping(str, Enum):
    WINS = "wins"
    KILLS = "kills"
    DAMAGE = "damage"


class CDataTrackerMode(str, Enum):
    BR = "br"
    ARENAS = "arenas"


class RespawnCData(BaseDBModel):
    c_data: int
    value: str
    key: str
    category: CDataCategory


class RespawnCDataTracker(RespawnCData):
    grouping: CDataTrackerGrouping
    mode: CDataTrackerMode


class RespawnCDataCollection(BaseDBCollection):

    def retrieve_one(self, uuid: UUID) -> RespawnCData:
        return RespawnCData(
            collection=self.collection,
            **self.find_one(uuid)
        )

    def retrieve_all(self, criteria: dict = None) -> List[RespawnCData]:
        retrieved_records: List[RespawnCData] = list()
        for record in self.find_many(criteria):
            retrieved_records.append(RespawnCData(collection=self.collection, **record))
        return retrieved_records


def try_cdata_test():
    from apex_db_helper import ApexDBHelper

    db_collection: Collection = ApexDBHelper().database.respawn_cdata

    collection: RespawnCDataCollection = RespawnCDataCollection(db_collection)
    record: RespawnCData
    for record in collection.retrieve_all():
        print(record)
    print(len(collection.retrieve_all()))


def clean_up_respawn_cdata_db():
    """ Go through all the records that don't have UUID's and add them """
    from apex_db_helper import ApexDBHelper

    collection: Collection = ApexDBHelper().database.respawn_cdata
    count: int = 1
    for record in collection.find({'uuid': {'$exists': False}}):
        if not record.get('uuid'):
            print(f"Updating UUID: {count}")
            count += 1
            record['uuid'] = uuid4()
            collection.update_one(
                filter={'c_data': record['c_data']},
                update={"$set": record}
            )


if __name__ == '__main__':
    # clean_up_respawn_cdata_db()
    try_cdata_test()
