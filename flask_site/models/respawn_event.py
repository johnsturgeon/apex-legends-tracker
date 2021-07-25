""" Dataclass to represent respawn event collection """
from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache, cached_property
from typing import List
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pydantic import PrivateAttr

# pylint: disable=import-error
from instance.config import get_config
from models import RespawnRecord, RespawnRecordCollection, CDataCollection, PlayerCollection
from models.respawn_cdata import CDataTrackerValue
from models.base_db_model import BaseDBModel, BaseDBCollection

config = get_config(os.getenv('FLASK_ENV'))


# pylint: disable=missing-class-docstring
class CDataTrackerException(Exception):
    pass


class RespawnEventException(Exception):
    pass


class RespawnEventType(str, Enum):
    GAME = "Game"


class RespawnEvent(BaseDBModel):
    respawn_record_collection: RespawnRecordCollection
    cdata_collection: CDataCollection
    player_collection: PlayerCollection
    _exclude = {'respawn_record_collection', 'cdata_collection', 'player_collection'}

    uuid: UUID
    event_type: RespawnEventType
    before_event_record_uuid: UUID
    after_event_record_uuid: UUID
    _before_respawn_record: RespawnRecord = PrivateAttr(None)
    _after_respawn_record: RespawnRecord = PrivateAttr(None)

    @property
    def unique_key(self) -> dict:
        return {'uuid': self.uuid}

    @property
    def before_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        return self.respawn_record_collection.retrieve_one(self.before_event_record_uuid)

    @property
    def after_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        return self.respawn_record_collection.retrieve_one(self.after_event_record_uuid)

    @property
    def player_uid(self) -> int:
        """ returns the player's uid """
        return self.before_respawn_record.uid


class RespawnGameEvent(RespawnEvent):

    @property
    def game_length(self) -> int:
        """ Returns the length of the game in seconds """
        after_record: RespawnRecord = self.after_respawn_record
        before_record: RespawnRecord = self.before_respawn_record
        return round((after_record.timestamp - before_record.timestamp) / 60)

    @property
    def player_name(self) -> str:
        """ returns the player's gamer tag (name) """
        player = self.player_collection.get_tracked_player_by_uid(self.player_uid)
        return player.name

    @property
    def timestamp(self) -> int:
        """ returns timestamp (UTC) """
        return self.after_respawn_record.timestamp

    @property
    def xp_progress(self) -> int:
        """ returns the xp_progress """
        progress_per_level: int = 18000
        after_record: RespawnRecord = self.after_respawn_record
        before_record: RespawnRecord = self.before_respawn_record
        level_progress: int = (
                after_record.account_level - before_record.account_level
        ) * progress_per_level
        level_progress += (
            after_record.account_progress_int - before_record.account_progress_int
        ) * progress_per_level / 100
        return int(level_progress)

    @property
    def legend(self) -> str:
        """ returns the 'legend' used for this event """
        return self.after_respawn_record.legend.value

    @property
    def trackers(self) -> List[CDataTrackerValue]:
        """ Returns the three trackers regardless of value """
        game_trackers = list()
        if len(self.after_respawn_record.tracker_values) != \
                len(self.before_respawn_record.tracker_values):
            raise CDataTrackerException
        index = 0
        tracker: CDataTrackerValue
        for tracker in self.after_respawn_record.tracker_values:
            before_tracker = self.before_respawn_record.tracker_values[index]
            value_change: int = tracker.value - before_tracker.value
            game_tracker: CDataTrackerValue = CDataTrackerValue(
                cdata_tracker=tracker.cdata_tracker,
                value=value_change
            )
            game_trackers.append(game_tracker)
            index += 1
        return game_trackers


class RespawnEventCollection(BaseDBCollection):

    def __init__(self,
                 db_collection: Collection,
                 respawn_record_collection: RespawnRecordCollection,
                 cdata_collection: CDataCollection,
                 player_collection: PlayerCollection
                 ):
        super().__init__(db_collection)
        self.respawn_record_collection = respawn_record_collection
        self.cdata_collection = cdata_collection
        self.player_collection = player_collection

    def obj_from_record(self, record: dict) -> RespawnEvent:
        return RespawnEvent(
            db_collection=self.db_collection,
            respawn_record_collection=self.respawn_record_collection,
            cdata_collection=self.cdata_collection,
            player_collection=self.player_collection,
            **record
        )

    @lru_cache
    def retrieve_one_record(self, uuid: UUID) -> dict:
        """ Guaranteed to return one record """
        record = self.find_one({'uuid': uuid})
        if not record:
            raise RespawnEventException(f"Record not found for uuid: {uuid}")
        return record

    @lru_cache
    def retrieve_one(self, uuid: UUID) -> RespawnEvent:
        """ Retrieves one record """
        return self.obj_from_record(self.retrieve_one_record(uuid))

    @lru_cache
    def retrieve_many(self) -> List[RespawnEvent]:
        """ Retrieves a list of records """
        retrieved_records: List[RespawnEvent] = list()
        for record in self.find_many():
            retrieved_records.append(
                self.obj_from_record(record)
                )
        return retrieved_records

    @cached_property
    def respawn_game_event_collection(self):
        """ Returns the respawn game event collection """
        return RespawnGameEventCollection(
            db_collection=self.db_collection,
            respawn_record_collection=self.respawn_record_collection,
            cdata_collection=self.cdata_collection,
            player_collection=self.player_collection
        )


class RespawnGameEventCollection(RespawnEventCollection):

    def obj_from_record(self, record: dict) -> RespawnGameEvent:
        return RespawnGameEvent(
            db_collection=self.db_collection,
            respawn_record_collection=self.respawn_record_collection,
            cdata_collection=self.cdata_collection,
            player_collection=self.player_collection,
            **record
        )

    @lru_cache
    def retrieve_one(self, uuid: UUID) -> RespawnGameEvent:
        return self.obj_from_record(self.retrieve_one_record(uuid))

    @lru_cache
    def retrieve_many(self) -> List[RespawnGameEvent]:
        retrieved_records: List[RespawnGameEvent] = list()
        for record in self.find_many():
            retrieved_records.append(
                self.obj_from_record(record)
            )
        return retrieved_records


def add_uuid_to_respawn_event():
    """ Go through all the records that don't have UUID's and add them """
    # pylint: disable=import-outside-toplevel
    from apex_db_helper import ApexDBHelper

    collection: Collection = ApexDBHelper().database.respawn_event
    count: int = 1
    for record in collection.find({'uuid': {'$exists': False}}):
        if not record.get('uuid'):
            print(f"Updating UUID: {count}")
            count += 1
            record['uuid'] = uuid4()
            collection.update_one(
                filter={
                    'after_event_record_uuid': record['after_event_record_uuid'],
                    'before_event_record_uuid': record['before_event_record_uuid']
                },
                update={"$set": record}
            )


def get_games():
    """ print each game"""
    # pylint: disable=import-outside-toplevel
    # from apex_db_helper import ApexDBHelper
    # db_helper = ApexDBHelper()
    # for sample_game in db_helper.respawn_game_event_collection.retrieve_many():
    #     print(f"eventType: {sample_game.event_type}")
    #     print(f"player_uid: {sample_game.player_uid}")
    #     print(f"player_name: {sample_game.player_name}")
    #     print(f"timestamp: {sample_game.timestamp}")
    #     print(f"game_length: {sample_game.game_length}")
    #     print(f"xp_progress: {sample_game.xp_progress}")
    #     print(f"legend: {sample_game.legend}")
    #     tracker: CDataTrackerValue
    #     for tracker in sample_game.trackers:
    #         tracker_detail: CDataTracker = tracker.cdata_tracker
    #         print(f"{tracker_detail.tracker_grouping.value}: {tracker.value}")
    #     print("===========================")
    #     print(sample_game.json())
    #
    # print(len(db_helper.respawn_game_event_collection.retrieve_many()))


if __name__ == '__main__':
    # add_uuid_to_respawn_event()
    get_games()
