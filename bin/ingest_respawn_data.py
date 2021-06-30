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
logger = config.logger(os.path.basename(__file__))
db_helper = ApexDBHelper()


class RespawnRecordNotFoundException(Exception):
    """ Simple exception for passing when a Respawn Record is not found"""


async def monitor_player(player: Player):
    """ daemon job that polls respawn """
    message = f"Starting monitor for {player.name}"
    logger.info(message)
    previous_record: RespawnRecord = await get_respawn_obj_from_stryder(
        player.uid, player.platform
    )
    if not previous_record:
        raise RespawnRecordNotFoundException

    slowdown = 0.0
    delay = 5.0 if previous_record and previous_record.online else 30.0
    while True:
        if previous_record and previous_record.online:
            logger.debug("%s is ONLINE (delay is %s)", player.name, delay)
        else:
            logger.debug(" - %s is offline (delay is %s)", player.name, delay)
        await asyncio.sleep(delay + slowdown)
        try:
            fetched_record: Optional[RespawnRecord] = await get_respawn_obj_from_stryder(
                player.uid, player.platform
            )
        except RespawnSlowDownException:
            slowdown += 20.0
            message = f"Slowing down from {delay} to {delay + slowdown}"
            logger.warning(message)
            continue
        if slowdown:
            slowdown -= .5
            message = f"Speeding up from {delay} to {delay + slowdown}"
            logger.warning(message)
        if not fetched_record:
            raise RespawnRecordNotFoundException
        save_record_if_changed(previous_record, fetched_record)
        delay = 5.0 if fetched_record.online else 30.0
        previous_record = fetched_record


def save_record_if_changed(previous_record, fetched_record):
    """ Saves a record if it has changed """
    collection: RespawnCollection = RespawnCollection(db_helper.database)
    if not previous_record:
        return
    if previous_record.online != fetched_record.online:
        if previous_record.online:
            message = f"{previous_record.name} logging off!"
        else:
            message = f"{previous_record.name} going ONLINE!"
        logger.info(message)
    prev_dict: dict = previous_record.dict(exclude={'timestamp'})
    fetched_dict: dict = fetched_record.dict(exclude={'timestamp'})
    if prev_dict != fetched_dict:
        value = {
            k: fetched_dict[k] for k, _ in set(
                fetched_dict.items()
            ) - set(prev_dict.items())
        }
        message = f"UPDATING {previous_record.name}: Player record changed: {value}"
        logger.info(message)
        collection.save_respawn_record(fetched_record)


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
    logger.info("Getting respawn data")
    for player in players:
        task_list.append(monitor_player(player))
    return await asyncio.gather(*task_list)


if __name__ == "__main__":
    asyncio.run(main())
