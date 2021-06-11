""" Dataclass to represent basic_info collection """
from dataclasses import dataclass, field
from typing import List, Tuple
import pymongo
import arrow
from mashumaro.config import BaseConfig, TO_DICT_ADD_OMIT_NONE_FLAG
from mashumaro import DataClassDictMixin, field_options
from pymongo.collection import Collection

from apex_utilities import get_arrow_date_to_use
from basic_info import BasicInfoCollection, BasicInfo, RankedSplit
from tracker_info import TrackerInfoCollection


# pylint: disable=missing-class-docstring
@dataclass
class GameTracker(DataClassDictMixin):
    value: int
    key: str
    name: str


# pylint: disable=too-many-instance-attributes
@dataclass
class GameEvent(DataClassDictMixin):
    uid: str
    player: str
    timestamp: int
    event: List[GameTracker]
    game_length: int = field(metadata=field_options(alias="gameLength"))
    legend_played: str = field(metadata=field_options(alias="legendPlayed"))
    rank_score_change: str = field(metadata=field_options(alias="rankScoreChange"))
    xp_progress: int = field(metadata=field_options(alias="xpProgress"))
    event_type: str = field(metadata=field_options(alias="eventType"))
    current_rank_score: str = field(default=-1, metadata=field_options(alias="currentRankScore"))
    _day_of_event: str = None
    kills: int = 0
    wins: int = 0
    damage: int = 0

    @property
    def day_of_event(self) -> str:
        """ Returns the 'day' of the event formatted 'YYYY-MMM-DD' (Pacific time) """
        if not self._day_of_event:
            self._day_of_event = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        return self._day_of_event

    def category_total(self, category) -> int:
        """ safely returns the category total - 0 if none exists """
        if hasattr(self, category):
            return getattr(self, category)
        return 0

    class Config(BaseConfig):
        """ Config class """
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]


class EventCollection:
    """ Class for abstracting the event collection """
    def __init__(self,
                 event_collection: Collection,
                 basic_info_collection: Collection,
                 tracker_info_collection: Collection
                 ):
        self._db_collection: Collection = event_collection
        self._basic_info_collection: BasicInfoCollection = BasicInfoCollection(
            basic_info_collection
        )
        self._tracker_info_collection: TrackerInfoCollection = TrackerInfoCollection(
            tracker_info_collection
        )

    def get_games(self,
                  player_uid: int = 0,
                  start_end_day: Tuple[str, str] = None,
                  additional_filter: dict = None,
                  sort: int = pymongo.ASCENDING) -> List[GameEvent]:
        """

        Args:
            sort (): defines sort order 1 ascending -1 descending
            additional_filter (): query filter for the 'event' db
            start_end_day (): format 'YYYY-MM-DD'
            player_uid (): filter by player (optional)

        Returns:

        """
        query_filter: dict = {
            "eventType": "Game"
        }
        if player_uid:
            query_filter['uid'] = str(player_uid)
        if start_end_day:
            start_day, end_day = start_end_day
            start_timestamp = get_arrow_date_to_use(start_day).int_timestamp
            end_timestamp = get_arrow_date_to_use(end_day).int_timestamp
            query_filter['timestamp'] = {"$gt": start_timestamp, "$lt": end_timestamp}
        if additional_filter:
            query_filter.update(additional_filter)

        event_list: list = self.get_event(query_filter, sort)

        game_list: List[GameEvent] = []
        for game in event_list:
            game_event: GameEvent = GameEvent.from_dict(game)
            self.update_game_category_totals(game_event)
            game_list.append(game_event)
        return game_list

    def get_ranked_games(self,
                         player_uid: int = 0,
                         season_number: int = 0,
                         split_number: int = 0
                         ) -> List[GameEvent]:
        """
        Returns a list of 'filtered' games based on season / split (current if none given)
        Args:
            player_uid:  Player UID for ranked games (default all players)
            season_number: Season number must be less than or equal to the current season
            split_number: Split number (cannot be zero of season given)

        Returns:
            List of all ranked game events
        """
        basic_info: BasicInfo = self._basic_info_collection.basic_info

        if season_number:
            assert split_number
            assert season_number <= basic_info.current_season
        current_ranked_split: RankedSplit = basic_info.get_ranked_split(
            season_number=season_number,
            split_number=split_number
        )
        query_filter: dict = {
            "rankScoreChange": {
                "$ne": "0"
            },
            "currentRankScore": {
                "$exists": True
            }
        }
        return self.get_games(
            player_uid,
            start_end_day=(current_ranked_split.start_date, current_ranked_split.end_date),
            additional_filter=query_filter
        )

    def update_game_category_totals(self, game: GameEvent):
        """ Checks the game event to see if it has the category, and adds it """
        tracker: GameTracker
        for tracker in game.event:
            tracker_cat: str = self._tracker_info_collection.category_for_key(
                tracker.key
            )
            if hasattr(game, tracker_cat):
                setattr(game, tracker_cat, tracker.value)
        # Category not found

    def get_event(self, query_filter: dict, sort_order: int = 0) -> list:
        """ Query the DB for events based on filter """
        assert sort_order in (pymongo.ASCENDING, 0, pymongo.DESCENDING)
        if sort_order:
            return list(
                self._db_collection.find(query_filter).sort('timestamp', sort_order)
            )
        return list(self._db_collection.find(query_filter))

    def save_event(self, event_data: dict):
        """ Saves any 'new' event data record """
        uid = event_data['uid']
        timestamp = event_data['timestamp']
        event_type = event_data['eventType']
        query_filter = {"uid": uid, "timestamp": timestamp, "eventType": event_type}
        db_data = self.get_event(query_filter)
        if not db_data:
            self._db_collection.insert_one(event_data)
