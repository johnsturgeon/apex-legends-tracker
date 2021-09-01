""" Process respawn data looking for events """
import os

from apex_db_helper import ApexDBHelper
from models import RespawnRecord, RespawnIngestionTaskCollection
# pylint: disable=import-error
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))
logger = config.logger(os.path.basename(__file__))
db_helper = ApexDBHelper()
ingestion_task_collection: RespawnIngestionTaskCollection = RespawnIngestionTaskCollection(
    db_helper.database
)


def is_game_event(previous_record: RespawnRecord, current_record: RespawnRecord):
    """ Checks to see if the event was a 'game' event """
    return previous_record.player_in_match != current_record.player_in_match


def main():
    """ Gets all unprocessed records and decides what to do with them """
    # to_process: List[RespawnRecord] = db_helper.respawn_record_collection.get_records()
    # games: List[RespawnEvent] = []
    # if to_process:
    #     previous_record: RespawnRecord = to_process.pop(0)
    #     game_start_uuid: Optional[UUID] = None
    #     for record in to_process:
    #         if is_game_event(previous_record, record):
    #             if record.player_in_match:
    #                 game_start_uuid = record.uuid
    #             else:
    #                 if game_start_uuid:
    #                     games.append(RespawnEvent(
    #                         db_collection=db_helper.database.respawn_event,
    #                         respawn_record_collection=db_helper.database.respawn_record,
    #                         event_type=RespawnEventType.GAME,
    #                         before_event_record_uuid=game_start_uuid,
    #                         after_event_record_uuid=record.uuid
    #                     ))
    #                     game_start_uuid = None
    #         previous_record = record
    # for game in games:
    #     game.save()
    #     print(game.event_length())


if __name__ == "__main__":
    main()
