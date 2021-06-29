""" Ingest respawn data every 3 seconds """
import os
import asyncio
from typing import List, Optional

import arrow

from apex_api_helper import ApexAPIHelper, RespawnSlowDownException
from apex_db_helper import ApexDBHelper
from models import Player, RespawnRecord, RespawnCollection
# pylint: disable=import-error
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))

db_helper = ApexDBHelper()


class RespawnRecordNotFoundException(Exception):
    """ Simple exception for passing when a Respawn Record is not found"""


async def monitor_player(player: Player):
    """ daemon job that polls respawn """
    print(f"Starting monitor for {player.name}")
    previous_record: RespawnRecord = await get_respawn_obj_from_stryder(
        player.uid, player.platform
    )
    if not previous_record:
        raise RespawnRecordNotFoundException

    collection: RespawnCollection = RespawnCollection(db_helper.database)
    slowdown = 0.0
    delay = 5.0 if previous_record.online else 30.0
    while True:
        if previous_record.online:
            print(f"{player.name} is ONLINE (delay is {delay})")
        else:
            print(f" -- {player.name} is offline (delay is {delay})")
        await asyncio.sleep(delay + slowdown)
        try:
            fetched_record: Optional[RespawnRecord] = await get_respawn_obj_from_stryder(
                player.uid, player.platform
            )
        except RespawnSlowDownException:
            slowdown += 20.0
            message = f"Slowing down from {delay} to {delay + slowdown}"
            print(message)
            db_helper.logger.warning(message)
            continue
        if slowdown:
            slowdown -= .5
            message = f"Speeding up from {delay} to {delay + slowdown}"
            print(message)
            db_helper.logger.warning(message)
        if not fetched_record:
            raise RespawnRecordNotFoundException

        prev_dict: dict = previous_record.dict(exclude={'timestamp'})
        fetched_dict: dict = fetched_record.dict(exclude={'timestamp'})
        if prev_dict != fetched_dict:
            value = {
                k: fetched_dict[k] for k, _ in set(
                    fetched_dict.items()
                ) - set(prev_dict.items())
            }
            print(f"UPDATING {previous_record.name}: Player record changed: {value}")
            collection.save_respawn_record(fetched_record)
        previous_record = fetched_record


async def get_respawn_obj_from_stryder(
        player_uid: int,
        platform: str,
        delay: int = 0
) -> Optional[RespawnRecord]:
    """ Queries respawn, and returns a respawn object """
    await asyncio.sleep(delay)
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


async def main():
    """ Returns a list of respawn players for given list of players """
    players: List[Player] = db_helper.player_collection.get_tracked_players()
    task_list: list = []
    print("Getting respawn data")
    for player in players:
        task_list.append(monitor_player(player))
    return await asyncio.gather(*task_list)


if __name__ == "__main__":
    asyncio.run(main())
