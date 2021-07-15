""" Dataclass to represent respawn record collection """
from __future__ import annotations

import os
from typing import List, Optional
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pydantic import Field

# pylint: disable=import-error
from base_db_model import BaseDBModel, BaseDBCollection
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))


class PlayerNotFoundException(Exception):
    """ Simple exception for when a player is not found """


# pylint: disable=missing-class-docstring
class RespawnRecord(BaseDBModel):
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

    trackers: Optional[List[RespawnTracker]] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._exclude_attrs.add('trackers')

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True


class RespawnRecordCollection(BaseDBCollection):

    def retrieve_one(self, uuid: UUID) -> RespawnRecord:
        return RespawnRecord(
            collection=self.collection,
            **self.collection.find_one({'uuid': uuid})
        )

    def retrieve_all(self, criteria: dict = None) -> List[RespawnRecord]:
        retrieved_records: List[RespawnRecord] = list()
        for record in self.collection.find(filter=criteria):
            retrieved_records.append(RespawnRecord(collection=self.collection, **record))
        return retrieved_records


def clean_up_respawn_record_db():
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


if __name__ == '__main__':
    clean_up_respawn_record_db()
