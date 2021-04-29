""" Helper module for """
import os
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

    def get_tracked_players(self) -> list:
        """ Return a list of dictionaries containing each player's data"""
        player_dict: dict = dict()
        for player in self.basic_player_collection.find():
            glob = player['global']
            player_dict[glob['uid']] = {
                'uid': glob['uid'],
                'name': glob['name'],
                'platform': glob['platform']
            }

        return list(player_dict.values())

    def save_player_data(self, player_data: dict):
        """ Saves a player_data record if it's changed """
        uid = player_data['global']['uid']
        internal_update_count = player_data['global']['internalUpdateCount']
        db_data = self.basic_player_collection.find_one(
            {"global.uid": uid, "global.internalUpdateCount": internal_update_count}
        )
        if not db_data:
            print(f"Inserting updated record for {player_data['global']['name']}")
            self.basic_player_collection.insert_one(player_data)

    def save_event_data(self, event_data: dict):
        """ Saves any 'new' event data record """
        uid = event_data['uid']
        timestamp = event_data['timestamp']
        event_type = event_data['eventType']
        db_data = self.event_collection.find_one(
            {"uid": uid, "timestamp": timestamp, "eventType": event_type}
        )
        if not db_data:
            print(f"Adding event for {event_data['player']}")
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
