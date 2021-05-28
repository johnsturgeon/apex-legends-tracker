""" Helper module for """
import os
import logging
import datetime
from logging import Logger
import arrow
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from apex_legends_api import ALPlayer
from apex_legends_api.al_domain import GameEvent, DataTracker

load_dotenv()


class LogHandler(logging.Handler):
    """
    A logging handler that will record messages to a capped MongoDB collection.
    """

    def __init__(self, client):
        """ Initialize the logger """
        level = getattr(logging, os.getenv('LOG_LEVEL'))
        logging.Handler.__init__(self, level)
        database: Database = client.apex_legends
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
class ApexDBHelper:
    """ Class for retrieving / saving data to the Apex Mongo DB """

    def __init__(self):
        uri = f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}"
        uri += f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
        uri += "?retryWrites=true&w=majority"
        self.client: MongoClient = MongoClient(uri)
        self.database: Database = self.client.apex_legends
        self.basic_player_collection: Collection = self.database.basic_player
        self.event_collection: Collection = self.database.event
        self.player_collection: Collection = self.database.player
        self.battlepass_info_collection: Collection = self.database.battlepass_info
        logger: Logger = logging.getLogger('apex_logger')
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL')))
        if not logger.handlers:
            logger.addHandler(LogHandler(self.client))
        self.logger = logger
        self._latest_event_timestamp: int = 0

    def get_player_by_uid(self, uid: int) -> ALPlayer:
        """
        Retrieve the ALPlayer object populated with data from the api.

        NOTE:
            Player must exist, method will return None if the player cannot be found

        :parameter uid: UID of the player
        :return: a single player or None if no player is found
        """
        basic_player_stats: dict = self.basic_player_collection.find_one(
            {"global.uid": uid}, sort=[("global.internalUpdateCount", -1)]
        )
        event_info: list = list(self.event_collection.find({'uid': str(uid)}))
        return ALPlayer(basic_player_stats_data=basic_player_stats, events=event_info)

    def get_tracked_players(self) -> list[dict]:
        """ Return a list of dictionaries containing each player's data"""
        return list(self.player_collection.find())

    def get_tracked_player_by_uid(self, uid: int):
        """ Returns one player given a uid """
        return self.player_collection.find_one(
            filter={'uid': uid}
        )

    def save_basic_player_data(self, player_data: dict):
        """ Saves a player_data record into `basic_player` if it's changed """
        uid = player_data['global']['uid']
        internal_update_count = player_data['global']['internalUpdateCount']
        key = {"global.uid": uid, "global.internalUpdateCount": internal_update_count}
        self.basic_player_collection.update_one(
            filter=key, update={"$set": player_data}, upsert=True
        )

    def save_player_data(self, player_data: dict):
        """ Saves player record """
        assert player_data.get('uid')
        key = {'uid': player_data['uid']}
        self.player_collection.update_one(filter=key, update={"$set": player_data}, upsert=True)

    def save_event_data(self, event_data: dict):
        """ Saves any 'new' event data record """
        uid = event_data['uid']
        timestamp = event_data['timestamp']
        event_type = event_data['eventType']
        db_data = self.event_collection.find_one(
            {"uid": uid, "timestamp": timestamp, "eventType": event_type}
        )
        if not db_data:
            self.logger.info(
                "Adding event for %s", event_data['player'])
            self.event_collection.insert_one(event_data)


class ApexDBGameEvent(GameEvent):
    """ Class for wrapping a game event """

    def __init__(self, event_dict: dict):
        super().__init__(event_dict)
        self.day = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        self._categories: dict = {}
        tracker: DataTracker
        for tracker in self.game_data_trackers:
            self._categories[tracker.category] = tracker.value
        self._categories['xp'] = self.xp_progress

    def category_total(self, category: str):
        """ returns the category total """
        total: int = self._categories.get(category)
        return total if total else 0

    def has_category(self, category: str) -> bool:
        """ Returns true if the game has a given category tracker """
        return category in self._categories


def filter_game_list(game_list: list,
                     category: str = None,
                     day: str = None,
                     legend: str = None,
                     uid: int = None
                     ) -> list:
    """ Returns a list of the games played on a specific day """
    filtered_list: list = []
    game: ApexDBGameEvent
    for game in game_list:
        found: bool = True
        if day and game.day != day:
            found = False
        if legend and game.legend_played != legend:
            found = False
        if category and not game.has_category(category):
            found = False
        if uid and int(game.uid) != uid:
            found = False
        if found:
            filtered_list.append(game)
    return filtered_list
