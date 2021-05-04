""" Helper module for """
import os
import logging
import datetime
from logging import Logger
import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from apex_legends_api import ALPlayer, ALPlatform
from apex_stats import PlayerData

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


class ApexDBHelper:
    """ Class for retrieving / saving data to the Apex Mongo DB """
    def __init__(self):

        self.client: MongoClient = MongoClient(
            host=os.getenv('MONGO_HOST'),
            username=os.getenv('MONGO_USERNAME'),
            password=os.getenv('MONGO_PASSWORD'),
            authSource=os.getenv('MONGO_DB'),
            authMechanism='SCRAM-SHA-256'
        )
        self.database: Database = self.client.apex_legends
        self.basic_player_collection: Collection = self.database.basic_player
        self.event_collection: Collection = self.database.event
        self.player_collection: Collection = self.database.player
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

    def get_tracked_players(self, active_only=False) -> list[dict]:
        """ Return a list of dictionaries containing each player's data"""
        player_dict: dict = dict()
        for player in self.player_collection.find():
            if not active_only or player['active']:
                basic_player = self.basic_player_collection.find_one(
                    filter={'global.uid': player['uid']},
                    sort=[("global.internalUpdateCount", pymongo.DESCENDING)]
                )
                glob = basic_player['global']
                realtime = basic_player['realtime']
                player_dict[glob['uid']] = {
                    'uid': int(glob['uid']),
                    'name': glob['name'],
                    'platform': glob['platform'],
                    'is_online': realtime['isOnline']
                }

        return list(player_dict.values())

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
        assert isinstance(player_data['uid'], int)
        key = {'uid': player_data['uid']}
        data = {
            'player_name': player_data['name'],
            'platform': player_data['platform'],
            'active': player_data['active']
        }
        self.player_collection.update_one(filter=key, update={"$set": data}, upsert=True)

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

    def get_platform_for_player_uid(self, player_uid: str) -> ALPlatform:
        """ Helper method that returns the platform from the given player """
        players = self.get_tracked_players()
        platform = ALPlatform.PC
        for tracked_player in players:
            if tracked_player["uid"] == player_uid:
                platform = ALPlatform(value=tracked_player["platform"])
        return platform

    def get_player_names(self, player_uid: str) -> str:
        """ Return a player name for the given player UID """
        for player in self.get_tracked_players():
            if player['uid'] == player_uid:
                return player['name']

        return "NotFound"

    def get_legend_icon(self, legend_name: str) -> str:
        """ Return the icon of a legend """
        basic_player_stats: dict = self.basic_player_collection.find_one(
            {}, sort=[("global.internalUpdateCount", -1)]
        )
        if not legend_name:
            self.logger.critical("YIKES, should have a legend")

        return basic_player_stats['legends']['all'][legend_name]['ImgAssets']['icon']

    def get_latest_event_timestamp(self) -> int:
        """ returns the latest timestamp in the db """
        if not self._latest_event_timestamp:
            newest_record = self.event_collection.find_one(sort=[("timestamp", pymongo.DESCENDING)])
            self._latest_event_timestamp = newest_record['timestamp']
        return self._latest_event_timestamp

    def get_max_category_for_day(self, category: str, day: str) -> int:
        """ Returns the maximum category total for the day """
        max_category: int = 0
        for player in self.get_tracked_players():
            al_player: ALPlayer = self.get_player_by_uid(player['uid'])
            player_data: PlayerData = PlayerData(al_player)
            max_category = max(max_category, player_data.category_total(day, category))
        return max_category

    def get_max_category_avg_for_day(self, category: str, day: str) -> float:
        """ Returns the maximum category average for the day """
        max_avg_category: float = 0.0
        for player in self.get_tracked_players():
            al_player: ALPlayer = self.get_player_by_uid(player['uid'])
            player_data: PlayerData = PlayerData(al_player)
            max_avg_category = max(
                max_avg_category, player_data.category_day_average(day, category)
            )
        return max_avg_category
