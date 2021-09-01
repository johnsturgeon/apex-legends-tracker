""" Ingest respawn data every 3 seconds """
import os
import asyncio
from asyncio import Task
from typing import List, Optional
from uuid import uuid4

import arrow

from apex_api_helper import ApexAPIHelper, RespawnSlowDownException
from apex_db_helper import ApexDBHelper
from models import Player, RespawnRecord, RespawnIngestionTaskCollection
# pylint: disable=import-error
from instance.config import get_config
config = get_config(os.getenv('FLASK_ENV'))
logger = config.logger(os.path.basename(__file__))
db_helper = ApexDBHelper()
ingestion_task_collection: RespawnIngestionTaskCollection = RespawnIngestionTaskCollection(
    db_helper.database
)

ONLINE_DELAY = 15.0
OFFLINE_DELAY = 60.0


class TaskDiedException(Exception):
    """ Simple exception thrown if a task dies, we die. """


async def monitor_player(player: Player):
    """ daemon job that polls respawn """
    message = f"Starting monitor for {player.name}"
    logger.info(message)
    previous_record: RespawnRecord = await get_respawn_obj_from_stryder(
        player.uid, player.platform
    )
    if not previous_record:
        ingestion_task_collection.fetch_error(player.name)
        logger.warning("Respawn record not found -- continuing")

    slowdown = 0.0
    delay = ONLINE_DELAY if previous_record and previous_record.online else OFFLINE_DELAY
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
            ingestion_task_collection.fetch_error(player.name)
            continue
        if slowdown:
            slowdown -= .5
            message = f"Speeding up from {delay} to {delay + slowdown}"
            logger.warning(message)
        if not fetched_record:
            ingestion_task_collection.fetch_error(player.name)
            logger.warning("Respawn record not found -- continuing")
            continue
        ingestion_task_collection.fetched_record(player.name)
        save_record_if_changed(previous_record, fetched_record)
        delay = ONLINE_DELAY if fetched_record.online else OFFLINE_DELAY
        previous_record = fetched_record


def save_record_if_changed(previous_record: RespawnRecord, fetched_record: RespawnRecord):
    """ Saves a record if it has changed """
    if not previous_record:
        return
    if previous_record.online != fetched_record.online:
        if previous_record.online:
            message = f"{previous_record.name} logging off!"
        else:
            message = f"{previous_record.name} going ONLINE!"
        logger.info(message)
    prev_dict: dict = previous_record.dict(exclude={'timestamp', 'uuid'})
    fetched_dict: dict = fetched_record.dict(exclude={'timestamp', 'uuid'})
    if prev_dict != fetched_dict:
        value = {
            k: fetched_dict[k] for k, _ in set(
                fetched_dict.items()
            ) - set(prev_dict.items())
        }
        message = f"UPDATING {previous_record.name}: Player record changed: {value}"
        logger.info(message)
        ingestion_task_collection.inserted_record(fetched_record.name)
        fetched_record.save()


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
            db_collection=db_helper.database.respawn_record,
            cdata_collection=db_helper.cdata_collection,
            player_collection=db_helper.player_collection,
            uuid=uuid4(),
            timestamp=timestamp,
            **respawn_data['userInfo']
        ))
    return None


async def main():
    """ Returns a list of respawn players for given list of players """
    players: List[Player] = db_helper.player_collection.get_tracked_players()
    ingestion_task_collection.init_tasks(players)
    task_list: List[Task] = list()
    logger.info("Starting the Respawn Ingestion script")
    for player in players:
        task = asyncio.create_task(monitor_player(player))
        task.set_name(player.name)
        task_list.append(task)

    while True:
        await asyncio.sleep(120)
        for task in task_list:
            if task.done():
                logger.error("Task died: %s", {task.get_name()})
                raise TaskDiedException


if __name__ == "__main__":
    asyncio.run(main())
