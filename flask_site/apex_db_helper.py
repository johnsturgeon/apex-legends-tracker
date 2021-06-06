""" Helper module for """
import os
import logging
import datetime
from logging import Logger
from typing import List
import arrow
from dotenv import load_dotenv
from pymongo import MongoClient
import pymongo.database
from pymongo.collection import Collection
from apex_legends_api import ALPlayer
from apex_legends_api.al_domain import GameEvent, DataTracker
from models import BasicInfo, RankedGameEvent, RankedSplit, Player

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
        self.event_collection: Collection = self.database.event
        self.player_collection: Collection = self.database.player
        self._basic_info = None
        logger: Logger = logging.getLogger('apex_logger')
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL')))
        if not logger.handlers:
            logger.addHandler(LogHandler(self.client))
        self.logger = logger
        self._latest_event_timestamp: int = 0

    @property
    def basic_info(self) -> BasicInfo:
        """ Factory method for BasicInfo data """
        if getattr(self, '_basic_info', None) is None:
            self._basic_info = BasicInfo.from_dict(self.database.basic_info.find_one({}))
        return self._basic_info

    def get_ranked_games(self,
                         player_uid: int = 0,
                         season_number: int = 0,
                         split_number: int = 0
                         ) -> List[RankedGameEvent]:
        """
        Returns a list of 'filtered' games based on season / split (current if none given)
        Args:
            player_uid:  Player UID for ranked games (default all players)
            season_number: Season number must be less than or equal to the current season
            split_number: Split number (cannot be zero of season given)

        Returns:
            List of all ranked game events
        """
        basic_info: BasicInfo = self.basic_info
        if season_number:
            assert split_number
            assert season_number <= basic_info.current_season
        current_ranked_split: RankedSplit = basic_info.get_ranked_split(
            season_number=season_number,
            split_number=split_number
        )
        start_date = arrow.get(current_ranked_split.start_date).to('US/Pacific')
        end_date = arrow.get(current_ranked_split.end_date).to('US/Pacific')
        start_timestamp = start_date.int_timestamp
        end_timestamp = end_date.int_timestamp

        query_filter: dict = {
            "eventType": "Game",
            "rankScoreChange": {
                "$ne": "0"
            },
            "currentRankScore": {
                "$exists": True
            },
            "timestamp": {
                "$gt": start_timestamp,
                "$lt": end_timestamp
            }
        }
        if player_uid:
            query_filter['uid'] = str(player_uid)

        game_list: list = list(
            self.event_collection.find(query_filter).sort('timestamp', pymongo.ASCENDING)
        )
        ranked_game_list: List[RankedGameEvent] = []
        for game in game_list:
            ranked_game_list.append(RankedGameEvent.from_dict(game))
        return ranked_game_list

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

    def get_tracked_players(self) -> list[Player]:
        """ Return a list of dictionaries containing each player's data"""
        player_list: List[Player] = list()
        for player_data in self.player_collection.find():
            player_list.append(Player.from_dict(player_data))
        return player_list

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

    def save_player_data(self, player_data: Player):
        """ Saves player record """
        assert player_data.uid != 0
        key = {'uid': player_data.uid}
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
