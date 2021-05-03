""" Helper module for """
import os
import arrow
import pymongo
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from apex_legends_api import ALPlayer, ALPlatform

load_dotenv()


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
        print(
            f"{arrow.now().format()}: Inserting updated record for {player_data['global']['name']}"
        )
        result = self.basic_player_collection.update_one(
            filter=key, update={"$set": player_data}, upsert=True
        )
        if result:
            pass

    def save_player_data(self, player_data: dict):
        """ Saves player record """
        assert isinstance(player_data['uid'], int)
        key = {'uid': player_data['uid']}
        data = {
            'player_name': player_data['name'],
            'platform': player_data['platform'],
            'active': player_data['active']
        }
        result = self.player_collection.update_one(filter=key, update={"$set": data}, upsert=True)
        if result:
            pass

    def save_event_data(self, event_data: dict):
        """ Saves any 'new' event data record """
        uid = event_data['uid']
        timestamp = event_data['timestamp']
        event_type = event_data['eventType']
        db_data = self.event_collection.find_one(
            {"uid": uid, "timestamp": timestamp, "eventType": event_type}
        )
        if not db_data:
            print(f"{arrow.now().format()}: Adding event for {event_data['player']}")
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
            print("YIKES")
        return basic_player_stats['legends']['all'][legend_name]['ImgAssets']['icon']

    def get_latest_event_timestamp(self) -> int:
        """ returns the latest timestamp in the db """
        if not self._latest_event_timestamp:
            newest_record = self.event_collection.find_one(sort=[("timestamp", pymongo.DESCENDING)])
            self._latest_event_timestamp = newest_record['timestamp']
        return self._latest_event_timestamp

