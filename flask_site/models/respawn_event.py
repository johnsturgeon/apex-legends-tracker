""" Dataclass to represent respawn event collection """
from __future__ import annotations

import os
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from pymongo.collection import Collection
from pydantic import PrivateAttr

from base_db_model import BaseDBModel
# pylint: disable=import-error
from instance.config import get_config
from models import RespawnRecord

config = get_config(os.getenv('FLASK_ENV'))


# pylint: disable=missing-class-docstring
class RespawnEventType(str, Enum):
    GAME = "Game"


class RespawnEvent(BaseDBModel):
    respawn_record_collection: Collection
    event_type: RespawnEventType
    before_event_record_uuid: UUID
    after_event_record_uuid: UUID
    _before_respawn_record: RespawnRecord = PrivateAttr(None)
    _after_respawn_record: RespawnRecord = PrivateAttr(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._exclude_attrs.add('respawn_record_collection')

    @property
    def event_length(self) -> int:
        """ Returns the length of the event in seconds """
        return self.after_respawn_record.timestamp - self.before_respawn_record.timestamp

    @property
    def before_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        if self._before_respawn_record is None:
            record = self.respawn_record_collection.find_one({'uuid': self.before_event_record_uuid})
            self._before_respawn_record = RespawnRecord(**record)
        return self._before_respawn_record

    @property
    def after_respawn_record(self) -> RespawnRecord:
        """ returns the actual Respawn Record """
        if self._after_respawn_record is None:
            record = self.respawn_record_collection.find_one({'uuid': self.after_event_record_uuid})
            self._after_respawn_record = RespawnRecord(**record)
        return self._after_respawn_record


def clean_up_respawn_event_db():
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


if __name__ == '__main__':
    clean_up_respawn_event_db()
