""" Dataclass to represent respawn event collection """
from __future__ import annotations

import os
from enum import Enum
from typing import List, ClassVar, Any
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pydantic import PrivateAttr
from pymongo.database import Database

from base_db_model import BaseDBModel, BaseDBCollection
# pylint: disable=import-error
from instance.config import get_config
from models import RespawnRecord, RespawnRecordCollection, CDataCollection

config = get_config(os.getenv('FLASK_ENV'))


# pylint: disable=missing-class-docstring
class RespawnEventException(Exception):
    pass


class RespawnEventType(str, Enum):
    GAME = "Game"


class RespawnEvent(BaseDBModel):
    respawn_record_collection: RespawnRecordCollection
    _exclude = {'respawn_record_collection'}

    uuid: UUID
    event_type: RespawnEventType
    before_event_record_uuid: UUID
    after_event_record_uuid: UUID
    _before_respawn_record: RespawnRecord = PrivateAttr(None)
    _after_respawn_record: RespawnRecord = PrivateAttr(None)

    @property
    def cdata_collection(self) -> CDataCollection:
        return self.respawn_record_collection.cdata_collection

    @property
    def collection(self) -> Collection:
        return self.db.respawn_event

    @property
    def unique_key(self) -> dict:
        return {'uuid': self.uuid}

    @property
    def event_length(self) -> int:
        """ Returns the length of the event in seconds """
        after_record: RespawnRecord = self.after_respawn_record
        before_record: RespawnRecord = self.before_respawn_record
        return after_record.timestamp - before_record.timestamp

    @property
    def before_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        if self._before_respawn_record is None:
            record = self.respawn_record_collection.retrieve_one_record(self.before_event_record_uuid)
            self._before_respawn_record = RespawnRecord(
                db=self.db,
                cdata_collection=self.cdata_collection,
                **record
            )
        return self._before_respawn_record

    @property
    def after_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        if self._after_respawn_record is None:
            record = self.respawn_record_collection.retrieve_one_record(self.after_event_record_uuid)
            cdata_col: CDataCollection = self.cdata_collection
            if not isinstance(cdata_col, CDataCollection):
                print("YIKES")
            self._after_respawn_record = RespawnRecord(
                db=self.db,
                cdata_collection=self.cdata_collection,
                **record
            )
        return self._after_respawn_record

    @property
    def uid(self) -> int:
        return self._before_respawn_record.uid


class RespawnEventCollection(BaseDBCollection):

    def __init__(self,
                 db: Database,
                 respawn_record_collection: RespawnRecordCollection
                 ):
        super().__init__(db)
        self.respawn_record_collection = respawn_record_collection

    @property
    def collection(self) -> Collection:
        return self.db.respawn_event

    def retrieve_one_record(self, uuid: UUID) -> dict:
        """ Guaranteed to return one record """
        record = self.find_one({'uuid': uuid})
        if not record:
            raise RespawnEventException("Record not found for uuid: %s", uuid)
        return record

    def retrieve_many(self, criteria: dict = None) -> List[RespawnEvent]:
        retrieved_records: List[RespawnEvent] = list()
        for record in self.find_many(criteria):
            retrieved_records.append(
                RespawnEvent(
                    db=self.db,
                    respawn_record_collection=self.respawn_record_collection,
                    **record)
            )
        return retrieved_records


def add_uuid_to_respawn_event():
    """ Go through all the records that don't have UUID's and add them """
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
    from apex_db_helper import ApexDBHelper
    db = ApexDBHelper().database
    cdata_collection: CDataCollection = CDataCollection(
        db=db
    )
    respawn_record_collection: RespawnRecordCollection = RespawnRecordCollection(
        db=db,
        cdata_collection=cdata_collection
    )
    rs_event_collection: RespawnEventCollection = RespawnEventCollection(
        db=db,
        respawn_record_collection=respawn_record_collection
    )
    sample_game = rs_event_collection.retrieve_many()[0]
    print(f"eventType: {sample_game.event_type}")
    print(f"player: {sample_game.player}")


if __name__ == '__main__':
    # add_uuid_to_respawn_event()
    get_games()
