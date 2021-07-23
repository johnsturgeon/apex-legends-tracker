""" Dataclass to represent respawn record collection """
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import List
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pydantic import Field, PrivateAttr

# pylint: disable=import-error
from base_db_model import BaseDBModel, BaseDBCollection
from instance.config import get_config
from respawn_cdata import CDataTracker, CData, CDataTrackerValue
from models import CDataCollection, PlayerCollection

config = get_config(os.getenv('FLASK_ENV'))


class RespawnRecordException(Exception):
    pass


# pylint: disable=missing-class-docstring
class RespawnLegend(str, Enum):
    ALL = "all"
    BANGALORE = "bangalore"
    BLOODHOUND = "bloodhound"
    CAUSTIC = "caustic"
    CRYPTO = "crypto"
    FUSE = "fuse"
    GIBRALTAR = "gibraltar"
    HORIZON = "horizon"
    LIFELINE = "lifeline"
    LOBA = "loba"
    MIRAGE = "mirage"
    OCTANE = "octane"
    PATHFINDER = "pathfinder"
    RAMPART = "rampart"
    REVENANT = "revenant"
    VALKYRIE = "valkyrie"
    WATTSON = "wattson"
    WRAITH = "wraith"


class RespawnRecord(BaseDBModel):
    cdata_collection: CDataCollection
    player_collection: PlayerCollection
    _exclude = {'cdata_collection', 'player_collection'}

    uuid: UUID
    timestamp: int
    uid: int
    hardware: str
    name: str
    ban_reason: int = Field(alias='banReason')
    ban_seconds: int = Field(alias='banSeconds')
    rank_score: int = Field(alias='rankScore')
    arena_score: int = Field(alias='arenaScore')
    character: int = Field(alias='cdata2')
    character_skin: int = Field(alias='cdata3')
    banner_frame: int = Field(alias='cdata4')
    banner_stance: int = Field(alias='cdata5')
    banner_badge1: int = Field(alias='cdata6')
    banner_badge1_tier: int = Field(alias='cdata7')
    banner_badge2: int = Field(alias='cdata8')
    banner_badge2_tier: int = Field(alias='cdata9')
    banner_badge3: int = Field(alias='cdata10')
    banner_badge3_tier: int = Field(alias='cdata11')
    banner_tracker1: int = Field(alias='cdata12')
    banner_tracker1_value: int = Field(alias='cdata13')
    banner_tracker2: int = Field(alias='cdata14')
    banner_tracker2_value: int = Field(alias='cdata15')
    banner_tracker3: int = Field(alias='cdata16')
    banner_tracker3_value: int = Field(alias='cdata17')
    character_intro_quip: int = Field(alias='cdata18')
    account_level: int = Field(alias='cdata23')
    account_progress_int: int = Field(alias='cdata24')
    player_in_match: int = Field(alias='cdata31')
    online: int
    joinable: int
    party_full: int = Field(alias='partyFull')
    party_in_match: int = Field(alias='partyInMatch')

    _cdata_trackers: List[CDataTrackerValue] = PrivateAttr(default=list())

    class Config:
        allow_population_by_field_name = True
        exclude_unset = False

    @property
    def unique_key(self) -> dict:
        return {'uuid': self.uuid}

    @staticmethod
    def fixed_value(value: int) -> int:
        return int((value - 2) / 100)

    @property
    def tracker_values(self) -> List[CDataTrackerValue]:
        if not self._cdata_trackers:
            self._cdata_trackers = list()
            self._cdata_trackers.append(CDataTrackerValue(
                cdata_tracker=self.cdata_collection.tracker_collection.retrieve_one(
                    self.banner_tracker1
                ),
                value=RespawnRecord.fixed_value(self.banner_tracker1_value)
            ))
            self._cdata_trackers.append(CDataTrackerValue(
                cdata_tracker=self.cdata_collection.tracker_collection.retrieve_one(
                    self.banner_tracker2
                ),
                value=RespawnRecord.fixed_value(self.banner_tracker2_value)
            ))
            self._cdata_trackers.append(CDataTrackerValue(
                cdata_tracker=self.cdata_collection.tracker_collection.retrieve_one(
                    self.banner_tracker3
                ),
                value=RespawnRecord.fixed_value(self.banner_tracker3_value)
            ))
        return self._cdata_trackers
    
    @property
    def legend(self) -> RespawnLegend:
        legend_cdata: CData = self.cdata_collection.retrieve_legend(self.character)
        character_name: str = legend_cdata.name.lower()
        return RespawnLegend(value=character_name)


class RespawnRecordCollection(BaseDBCollection):

    def __init__(self,
                 db_collection: Collection,
                 cdata_collection: CDataCollection,
                 player_collection: PlayerCollection
                 ):
        super().__init__(db_collection)
        self.cdata_collection = cdata_collection
        self.player_collection = player_collection

    def obj_from_record(self, record: dict) -> RespawnRecord:
        return RespawnRecord(
            db_collection=self.db_collection,
            cdata_collection=self.cdata_collection,
            player_collection=self.player_collection,
            **record
        )

    @lru_cache
    def retrieve_one(self, uuid: UUID) -> RespawnRecord:
        return self.obj_from_record(self.retrieve_one_record(uuid))

    @lru_cache
    def retrieve_one_record(self, uuid: UUID) -> dict:
        """ Guaranteed to return one record """
        record = self.find_one({'uuid': uuid})
        if not record:
            raise RespawnRecordException("Record not found for uuid: %s", uuid)
        return record

    @lru_cache
    def retrieve_many(self,
                      gt_timestamp: int = None,
                      lt_timestamp: int = None,
                      name: str = None) -> List[RespawnRecord]:
        retrieved_records: List[RespawnRecord] = list()
        criteria: dict = dict()
        if gt_timestamp:
            criteria.update({
                'timestamp': {'$gt': gt_timestamp}
            })
        if lt_timestamp:
            criteria.update({
                'timestamp': {'$lt': gt_timestamp}
            })
        if name:
            criteria.update({
                'name': name
            })
        for record in self.find_many(criteria):
            retrieved_records.append(
                self.obj_from_record(record)
            )
        return retrieved_records


def add_uuid_to_respawn_record():
    """ Go through all the records that don't have UUID's and add them """
    from apex_db_helper import ApexDBHelper
    collection: Collection = ApexDBHelper().database.respawn_record
    count: int = 1
    for record in collection.find({'uuid': {'$exists': False}}):
        if not record.get('uuid'):
            print(f"Updating UUID: {count}")
            count += 1
            record['uuid'] = uuid4()
            collection.update_one(
                filter={'timestamp': record['timestamp'], 'uid': record['uid']},
                update={"$set": record}
            )


def print_records():
    from apex_db_helper import ApexDBHelper
    db_helper: ApexDBHelper = ApexDBHelper()
    records = db_helper.respawn_record_collection.retrieve_many(gt_timestamp=1626246000, name='GoshDarnedHero')
    for record in records:
        print(record.trackers)


if __name__ == '__main__':
    # add_uuid_to_respawn_record()
    print_records()
