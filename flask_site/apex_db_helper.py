""" Helper module for """
import os
import logging
import datetime
from logging import Logger
from typing import List

from dotenv import load_dotenv
from pymongo import MongoClient
import pymongo.database
from pymongo.collection import Collection

from event import EventCollection, GameEvent
from models import BasicInfoCollection, BasicInfo
from player import PlayerCollection

load_dotenv()


class LogHandler(logging.Handler):
    """
    A logging handler that will record messages to a capped MongoDB collection.
    """

    def __init__(self, client):
        """ Initialize the logger """
        level = getattr(logging, os.getenv('LOG_LEVEL'))
        logging.Handler.__init__(self, level)
        database: pymongo.database.Database = client.apex_legends
        self.log_collection: Collection = database.get_collection(os.getenv('LOG_COLLECTION'))

    def emit(self, record):
        """ Override of the logger method """
        self.log_collection.insert_one({
            'when': datetime.datetime.now(),
            'log_level': record.levelno,
            'level_name': record.levelname,
            'message': record.msg % record.args
        })


# pylint: disable=too-many-instance-attributes
class ApexDBHelper:  # noqa E0302
    """ Class for retrieving / saving data to the Apex Mongo DB """

    def __init__(self):
        uri = f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}"
        uri += f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
        uri += "?retryWrites=true&w=majority"
        self.client: MongoClient = MongoClient(uri)
        self.database: pymongo.database.Database = self.client.apex_legends
        self.basic_player_collection: Collection = self.database.basic_player
        self.event_collection: EventCollection = EventCollection(
            event_collection=self.database.event,
            basic_info_collection=self.database.basic_info,
            tracker_info_collection=self.database.tracker_info
        )
        self.player_collection: PlayerCollection = PlayerCollection(self.database.player)
        self.basic_info: BasicInfo = BasicInfoCollection(
            self.database.basic_info
        ).basic_info
        logger: Logger = logging.getLogger('apex_logger')
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL')))
        if not logger.handlers:
            logger.addHandler(LogHandler(self.client))
        self.logger = logger
        self._latest_event_timestamp: int = 0

    def save_basic_player_data(self, player_data: dict):
        """ Saves a player_data record into `basic_player` if it's changed """
        uid = player_data['global']['uid']
        internal_update_count = player_data['global']['internalUpdateCount']
        key = {"global.uid": uid, "global.internalUpdateCount": internal_update_count}
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
    event_objects = db_helper.event_collection.get_event_objects()
    for event in event_objects:
        if event.event_type.value == 'Rank':
            print(event.event_type)
