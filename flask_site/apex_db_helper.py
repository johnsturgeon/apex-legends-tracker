""" Helper module for """
import json
import os
from typing import List

from pymongo import MongoClient
import pymongo.database
from pymongo.collection import Collection

from models import EventCollection, GameEvent, Config, PlayerCollection, ConfigCollection
from models import SeasonCollection, RespawnRecordCollection, RespawnIngestionTaskCollection

# pylint: disable=import-error
from instance.config import get_config

config = get_config(os.getenv('FLASK_ENV'))

# pylint: disable=too-many-instance-attributes
class ApexDBHelper:  # noqa E0302
    """ Class for retrieving / saving data to the Apex Mongo DB """

    def __init__(self):
        self.client: MongoClient = MongoClient(
            host=config.MONGO_HOST,
            username=config.MONGO_USERNAME,
            password=config.MONGO_PASSWORD,
            authSource=config.MONGO_DB
        )

        self.database: pymongo.database.Database = self.client.apex_legends
        self.basic_player_collection: Collection = self.database.basic_player
        self.event_collection: EventCollection = EventCollection(
            self.database,
            tracker_info_data=self.load_data('tracker_info.json')
        )
        self.player_collection: PlayerCollection = PlayerCollection(self.database)
        self.respawn_ingestion_task_collection: RespawnIngestionTaskCollection =\
            RespawnIngestionTaskCollection(self.database)
        self.season_collection: SeasonCollection = SeasonCollection(self.load_data('season.json'))
        self.config: Config = ConfigCollection(self.load_data('config.json')).config
        self.logger = config.logger(__name__)
        self._latest_event_timestamp: int = 0

    @staticmethod
    def load_data(filename: str) -> dict:
        """ Returns a dictionary representation of a json file"""
        file_path = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.abspath(file_path + "/models/static_data/" + filename)

        with open(filepath) as json_file:
            return json.load(json_file)

    def save_basic_player_data(self, player_data: dict):
        """ Saves a player_data record into `basic_player` if it's changed """
        if not player_data.get('global'):
            self.logger.warning("'global' not found in player data: %s", player_data)
            return
        uid = player_data['global']['uid']
        internal_update_count = player_data['global']['internalUpdateCount']
        key = {"global.uid": uid, "global.internalUpdateCount": internal_update_count}
        one_record = self.basic_player_collection.find_one(key)
        if not one_record:
            self.basic_player_collection.update_one(
                filter=key, update={"$set": player_data}, upsert=True
            )


def filter_game_list(game_list: List[GameEvent],
                     category: str = None,
                     day: str = None,
                     legend: str = None,
                     uid: int = None
                     ) -> list:
    """ Returns a list of the games played on a specific day """
    filtered_list: list = []
    game: GameEvent
    for game in game_list:
        found: bool = True
        if day and game.day_of_event != day:
            found = False
        if legend and game.legend_played != legend:
            found = False
        if category and not hasattr(game, category):
            found = False
        if uid and int(game.uid) != uid:
            found = False
        if found:
            filtered_list.append(game)
    return filtered_list


if __name__ == "__main__":
    db_helper: ApexDBHelper = ApexDBHelper()
    for basic_player_data in db_helper.database.dup_basic_player.find({}):
        db_helper.save_basic_player_data(basic_player_data)
