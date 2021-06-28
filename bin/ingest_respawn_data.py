""" Ingest respawn data every 3 seconds """
import os
import time
import asyncio
from typing import List, Optional

import arrow

from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from models import Player, RespawnRecord, RespawnCollection
from instance.config import get_config

# pylint: disable=import-error
config = get_config(os.getenv('FLASK_ENV'))
db_helper = ApexDBHelper()


async def get_respawn_obj_from_stryder(player_uid: int, platform: str) -> Optional[RespawnRecord]:
    """ Queries respawn, and returns a respawn object """
    respawn_data: Optional[dict] = await ApexAPIHelper.get_stryder_data(
        player_uid=player_uid,
        platform=platform
    )
    if respawn_data:
        utc_time = arrow.utcnow()
        timestamp = utc_time.int_timestamp
        return (RespawnRecord(
            timestamp=timestamp, **respawn_data['userInfo']
        ))
    return None


async def get_respawn_data_for_players(players: List[Player]):
    """ Returns a list of respawn players for given list of players """
    task_list: list = []
    print("Getting respawn data")
    for player in players:
        task_list.append(get_respawn_obj_from_stryder(player.uid, player.platform))
    return await asyncio.gather(*task_list)


async def main():
    """ Main loop = NEVER STOPS! :) """
    players: List[Player] = db_helper.player_collection.get_tracked_players()
    previous_respawn_records = await get_respawn_data_for_players(players)
    collection: RespawnCollection = RespawnCollection(db_helper.database)
    while True:
        time.sleep(3)
        fetched_respawn_records = await get_respawn_data_for_players(players)
        previous_record: RespawnRecord
        index: int = 0
        for previous_record in previous_respawn_records:
            fetched_record: RespawnRecord = fetched_respawn_records[index]
            if not previous_record or not fetched_record:
                db_helper.logger.warning("Got None for a record, request must have timed out")
                continue
            if fetched_record.online:
                print(f"{fetched_record.name} is online!")
            prev_dict: dict = previous_record.dict(exclude={'timestamp'})
            fetched_dict: dict = fetched_record.dict(exclude={'timestamp'})
            if prev_dict != fetched_dict:
                value = {
                    k: fetched_dict[k] for k, _ in set(
                        fetched_dict.items()
                    ) - set(prev_dict.items())
                }
                print(f"UPDATING: Player record changed: {value} {previous_record.name}")
                collection.save_respawn_record(fetched_record)
            previous_respawn_records = fetched_respawn_records
            index += 1


if __name__ == "__main__":
    asyncio.run(main())
