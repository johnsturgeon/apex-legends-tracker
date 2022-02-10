""" Dataclass to represent respawn ingestion job collection """
from __future__ import annotations

from typing import List

import pymongo.database

# pylint: disable=import-error
from instance.config import get_config
from models import Player

config = get_config('development')


class RespawnIngestionTaskCollection:
    """ Collection object for inserting records into the db """
    def __init__(self, database: pymongo.database.Database):
        self._collection: pymongo.collection.Collection = database.respawn_ingestion_task

    def init_tasks(self, players: List[Player]):
        """ Clears the collection of previous records and creates new fresh ones """
        self._collection.delete_many({})
        for player in players:
            self._collection.update_one(
                filter={"player_name": player.name},
                update={
                    "$set": {
                        'player_name': player.name,
                        'records_fetched': 0,
                        'records_inserted': 0,
                        'fetch_errors': 0
                    },
                    '$currentDate': {'last_update': True}
                },
                upsert=True
            )

    def fetched_record(self, player_name: str):
        """ Saves one record to the respawn DB"""
        key_filter = {'player_name': player_name}
        self._collection.update_one(filter=key_filter, update={
            "$inc": {'records_fetched': 1},
            "$currentDate": {'last_update': True}
        })

    def inserted_record(self, player_name: str):
        """ Saves one record to the respawn DB"""
        key_filter = {'player_name': player_name}
        self._collection.update_one(filter=key_filter, update={
            "$inc": {'records_inserted': 1},
            "$currentDate": {'last_update': True}
        })

    def fetch_error(self, player_name: str):
        """ Saves one record to the respawn DB"""
        key_filter = {'player_name': player_name}
        self._collection.update_one(filter=key_filter, update={
            "$inc": {'fetch_errors': 1},
            "$currentDate": {'last_update': True}
        })
