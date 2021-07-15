""" Process respawn data looking for events """
import os
from typing import List, Optional
from uuid import uuid4, UUID

import arrow

from apex_db_helper import ApexDBHelper
from models import RespawnRecord, RespawnIngestionTaskCollection
# pylint: disable=import-error
from instance.config import get_config
from respawn_event import RespawnEvent, RespawnEventType

config = get_config(os.getenv('FLASK_ENV'))
logger = config.logger(os.path.basename(__file__))
db_helper = ApexDBHelper()
ingestion_task_collection: RespawnIngestionTaskCollection = RespawnIngestionTaskCollection(
    db_helper.database
)


def is_game_event(previous_record: RespawnRecord, current_record: RespawnRecord):
    return previous_record.player_in_match != current_record.player_in_match


# Utility function
def update_uuid_on_respawn_records():
    for record in db_helper.respawn_record_collection.get_unprocessed_records():
        if record.uuid is None:
            record.uuid = uuid4()
        db_helper.respawn_record_collection.update_respawn_record(record)


def main():
    to_process: List[RespawnRecord] = db_helper.respawn_record_collection.get_unprocessed_records()
    games: List[RespawnEvent] = list()
    if to_process:
        previous_record: RespawnRecord = to_process.pop(0)
        game_start_uuid: Optional[UUID] = None
        for record in to_process:
            if is_game_event(previous_record, record):
                if record.player_in_match:
                    game_start_uuid = record.uuid
                else:
                    if game_start_uuid:
                        games.append(RespawnEvent(
                            collection=db_helper.database.respawn_event,
                            respawn_record_collection=db_helper.database.respawn_record,
                            event_type=RespawnEventType.GAME,
                            before_event_record_uuid=game_start_uuid,
                            after_event_record_uuid=record.uuid
                        ))
                        game_start_uuid = None
            previous_record = record
    for game in games:
        game.save()
        print(game.event_length())


if __name__ == "__main__":
    main()
