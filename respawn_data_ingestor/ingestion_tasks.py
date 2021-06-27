""" Script to scrape data from Respawn """
import time
from typing import List
import arrow

from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper

from models import Player, RespawnRecord, RespawnCollection
from models.respawn_record import PlayerNotFoundException
from .celery import app


def get_respawn_obj_from_stryder(player_uid: int, platform: str) -> RespawnRecord:
    """ Queries respawn, and returns a respawn object """
    respawn_data: dict = ApexAPIHelper.get_stryder_data(
        player_uid=player_uid,
        platform=platform
    )
    utc_time = arrow.utcnow()
    timestamp = utc_time.int_timestamp
    return RespawnRecord(
        timestamp=timestamp, **respawn_data['userInfo']
    )


def is_player_being_monitored(player_uid: int) -> bool:
    """
    Returns True if there is currently a celery job monitoring this player
    Args:
        player_uid ():

    Returns:
        Returns True if there is currently a celery job monitoring this player
    """
    print(f"checking to see if {player_uid} is online")
    i = app.control.inspect()
    for _, value in i.active().items():
        for job in value:
            if len(job['args']):
                if player_uid == job['args'][0]:
                    return True
    return False


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_):
    """ Sets up the periodic tasks for celery 'beat' """
    sender.add_periodic_task(60.0, check_online_status.s(), name='check online every 60')


@app.task(bind=True)
def ingest_respawn_data(self, player_uid: int, player_name: str, platform: str):
    """
    Long running task that adds any changed respawn data to the table for a given player
    while they're online
    Args:
        self ():
        player_uid (): uid of the player to track
        player_name (): name of the player (makes flower easier to see who's being tracked)
        platform (): necessary for respawn call
    """
    print("Ingest Respawn Data")
    apex_db_helper = ApexDBHelper()
    collection: RespawnCollection = RespawnCollection(apex_db_helper.database)
    print(f"Launching ingestion for {player_name} with {self.request.id}")
    previous_respawn_record: RespawnRecord = get_respawn_obj_from_stryder(
        player_uid=player_uid,
        platform=platform
    )
    if not previous_respawn_record:
        raise PlayerNotFoundException
    collection.save_respawn_record(previous_respawn_record)
    while True:
        time.sleep(3)
        fetched_respawn_record: RespawnRecord = get_respawn_obj_from_stryder(
            player_uid=player_uid,
            platform=platform
        )
        if previous_respawn_record.dict(exclude={'timestamp'}) != \
                fetched_respawn_record.dict(exclude={'timestamp'}):
            print('UPDATING: Player record changed: ' + previous_respawn_record.name)
            collection.save_respawn_record(fetched_respawn_record)
            previous_respawn_record = fetched_respawn_record
        if not previous_respawn_record.online:
            print(f"{player_name} has gone offline")
            return


@app.task
def check_online_status():
    """ task run every 60 seconds """
    apex_db_helper = ApexDBHelper()
    print("checking online status")
    players: List[Player] = apex_db_helper.player_collection.get_tracked_players()
    for player in players:
        # First, let's check to see if we need to remove any ingestion jobs from the db
        if is_player_being_monitored(player_uid=player.uid):
            print(f"There is a task monitoring {player.name} already running")
            continue

        respawn_data: dict = ApexAPIHelper.get_stryder_data(
            player_uid=player.uid,
            platform=player.platform
        )
        if respawn_data['userInfo']['online']:
            ingest_respawn_data.delay(player.uid, player.name, player.platform)
