""" Helper module for """
import os
import logging
import datetime
from enum import Enum
from logging import Logger
import pymongo
import arrow
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from apex_legends_api import ALPlayer, ALPlatform
from apex_legends_api.al_domain import GameEvent, DataTracker

load_dotenv()


class TrackerDataState(str, Enum):
    """ Sets the confidence level of the tracker data """
    NEVER_PLAYED = -2
    MISSING = -1
    OLD = 0
    CURRENT = 1

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            value = int(self.value)
            return value < int(other.value)
        return NotImplemented

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            value = int(self.value)
            return value == int(other.value)
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            value = int(self.value)
            return value > int(other.value)
        return NotImplemented

    def serialize(self):
        """ return json representation """
        return {
            'name': self.name,
            'value': self.value
        }


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
        uri = f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}"
        uri += f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
        uri += "?retryWrites=true&w=majority"
        self.client: MongoClient = MongoClient(uri)
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
                player_dict[player['uid']] = self.get_tracked_player_by_uid(player['uid'])

        return list(player_dict.values())

    def get_tracked_player_by_uid(self, uid: int):
        """ Returns one player given a uid """
        player = self.basic_player_collection.find_one(
            filter={'global.uid': uid},
            sort=[("global.internalUpdateCount", pymongo.DESCENDING)]
        )
        return {
            'uid': uid,
            'name': player['global']['name'],
            'platform': player['global']['platform'],
            'is_online': player['realtime']['isOnline']
        }

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

    def get_totals_for_legend(self, uid: int, legend_name: str, tracker_key: str) -> dict:
        """
        Returns the totals for a legend's tracker
        Args:
            uid (int): UID of the user to search
            legend_name (str): Legend name (i.e. Bangalore)
            tracker_key (str): Tracker key (i.e. `('kills', 'wins')`

        Returns:
            dict: Dictionary of results for legend

        Notes:
            `{ 'name': "Bangalor", 'total': 100,'tracker_statue': 1, 0, -1}`

            TrackerDataState: 1 = Confident, 0 = Not sure, -1 = Missing
        """
        total = 0
        tracker_state = TrackerDataState.NEVER_PLAYED
        key_search_set: set = {tracker_key, 'specialEvent_' + tracker_key}
        most_recently_selected = self.basic_player_collection.find_one(
            filter={"legends.selected.LegendName": legend_name, "global.uid": uid},
            sort=[("global.internalUpdateCount", pymongo.DESCENDING)]
        )
        if most_recently_selected:
            trackers = most_recently_selected['legends']['selected']['data']
            for tracker in trackers:
                tracker_key = tracker['key']
                if tracker_key in key_search_set:
                    total = tracker['value']
                    tracker_state = TrackerDataState.CURRENT
                    break
        if tracker_state < TrackerDataState.CURRENT:
            most_recent_record = self.basic_player_collection.find_one(
                filter={"global.uid": uid},
                sort=[("global.internalUpdateCount", pymongo.DESCENDING)]
            )
            trackers = most_recent_record['legends']['all'][legend_name].get('data')
            if trackers:
                tracker_state = TrackerDataState.MISSING
                for tracker in trackers:
                    tracker_key = tracker['key']
                    if tracker_key in key_search_set:
                        total = tracker['value']
                        tracker_state = TrackerDataState.OLD
                        break

        return {'name': legend_name, 'total': total, 'tracker_state': tracker_state}

    def get_inactive_legends(self, uid: int) -> list:
        """ Returns a list of the 'inactive' legends' """
        inactive_legends: list = []
        player = self.get_player_by_uid(uid)
        for legend in player.all_legends:
            most_recent_record = self.basic_player_collection.find_one(
                filter={"global.uid": uid},
                sort=[("global.internalUpdateCount", pymongo.DESCENDING)]
            )
            seen = most_recent_record['legends']['all'][legend].get('data')
            if not seen:
                inactive_legends.append(legend.name)
        return inactive_legends

    def get_player_totals(self, uid: int, tracker_keys: list, active_legends_only=False) -> dict:
        """
        Returns a list of legends and their totals

        Notes:
            TrackerDataState is based on 'worst case' state, so if *any*
            TrackerDataState is MISSING then we set the overall state to MISSING

        Examples:
            {
             'wins': {
                'total': 100,
                'tracker_state: 1, 0, -1,
                'legends': [{
                    'legend_name': 'Bangalore',
                    'total': 40,
                    'tracker_state: 1
                    },
                    ]
                }
            }
        """
        legend_totals_dict = {}
        player = self.get_player_by_uid(uid)
        for tracker_key in tracker_keys:
            legend_totals_dict[tracker_key] = {}
            key_totals_dict = legend_totals_dict[tracker_key]
            key_totals_dict['total'] = 0
            key_totals_dict['tracker_state'] = TrackerDataState.CURRENT
            key_totals_dict['legends']: list = []
            for legend in player.all_legends:
                one_legend_total_dict = self.get_totals_for_legend(uid, legend.name, tracker_key)
                key_totals_dict['total'] += one_legend_total_dict['total']
                inactive_legend = one_legend_total_dict[
                                      'tracker_state'
                                  ] == TrackerDataState.NEVER_PLAYED
                if not inactive_legend:
                    key_totals_dict['tracker_state'] = min(
                        key_totals_dict['tracker_state'], one_legend_total_dict['tracker_state']
                    )
                if inactive_legend and active_legends_only:
                    continue
                key_totals_dict['legends'].append(one_legend_total_dict)

        return legend_totals_dict


# pylint disable=too-few-public-methods
class ApexDBGameEvent(GameEvent):  # noqa R0903
    """ Class for wrapping a game event """

    def __init__(self, event_dict: dict):
        super().__init__(event_dict)
        self.day = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        self._categories: dict = {}
        tracker: DataTracker
        for tracker in self.game_data_trackers:
            self._categories[tracker.category] = tracker.value

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
        print(game.uid)
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
