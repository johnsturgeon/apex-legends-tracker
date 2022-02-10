""" Dataclass to represent event collection """
from typing import List, Tuple, Optional
from enum import Enum
import pymongo
import pymongo.database
import arrow
from pydantic import BaseModel, Field, PrivateAttr

from models.tracker_info import TrackerInfoCollection, GameMode
from models.season import Season
from apex_utilities import get_arrow_date_to_use


# pylint: disable=missing-class-docstring
# pylint: disable=too-many-instance-attributes
class EventType(str, Enum):
    SESSION = 'Session'
    GAME = 'Game'
    LEVEL = 'Level'
    RANK = 'Rank'


class BaseEvent(BaseModel):
    uid: str
    player: str
    timestamp: int
    event_type: EventType = Field(alias='eventType')

    def dict(self, **kwargs):
        return super().dict(
            by_alias=True,
            exclude_none=True,
            **kwargs
        )


class RankEventDetail(BaseModel):
    new_rank: str = Field(alias='newRank')
    new_rank_img: str = Field(alias='newRankImg')


class RankEvent(BaseEvent):
    event: RankEventDetail


class LevelEventDetail(BaseModel):
    new_level: int = Field(alias='newLevel')


class LevelEvent(BaseEvent):
    event: LevelEventDetail


class SessionAction(str, Enum):
    LEAVE = 'leave'
    JOIN = 'join'


class SessionEventDetail(BaseModel):
    action: SessionAction
    session_duration: Optional[int] = Field(alias='sessionDuration')


class SessionEvent(BaseEvent):
    event: SessionEventDetail


class GameEventDetail(BaseModel):
    value: int
    key: str
    name: str


class GameEvent(BaseEvent):
    event: List[GameEventDetail]
    game_length: int = Field(alias='gameLength')
    legend_played: str = Field(alias='legendPlayed')
    rank_score_change: str = Field(alias='rankScoreChange')
    xp_progress: int = Field(alias='xpProgress')
    kills: int = 0
    wins: int = 0
    damage: int = 0
    game_mode: Optional[GameMode] = None
    _day_of_event: str = PrivateAttr(None)
    _formatted_time: str = PrivateAttr(None)
    current_rank_score: Optional[str] = Field(alias='currentRankScore')

    @property
    def day_of_event(self) -> str:
        """ Returns the 'day' of the event formatted 'YYYY-MMM-DD' (Pacific time) """
        if not self._day_of_event:
            self._day_of_event = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        return self._day_of_event

    @property
    def formatted_time(self) -> str:
        """ Returns the formatted time of the event in Pacific """
        if not self._formatted_time:
            self._formatted_time = arrow.get(self.timestamp).to('US/Pacific').format('h:mma')
        return self._formatted_time

    @property
    def is_ranked_game(self) -> bool:
        """ Returns true if the ranked score change != 0 """
        return self.category_total('rank_score_change') != 0

    def category_total(self, category) -> int:
        """ safely returns the category total - 0 if none exists """
        if hasattr(self, category):
            total = getattr(self, category)
            if not isinstance(total, int):
                total = int(total)
            return total
        return 0

    def dict(self, **kwargs):
        return super().dict(exclude={'game_mode', 'kills', 'damage', 'wins'}, **kwargs)


class EventCollection:
    """ Class for abstracting the event collection """

    def __init__(self, database: pymongo.database.Database, tracker_info_data: dict):
        self._event_collection: pymongo.collection.Collection = database.event
        self._tracker_info_collection: TrackerInfoCollection = TrackerInfoCollection(
            tracker_info_data
        )

    # pylint: disable=too-many-arguments
    def get_games(self,
                  player_uid: int = 0,
                  start_end_day: Tuple[str, str] = None,
                  game_mode: Optional[GameMode] = None,
                  additional_filter: dict = None,
                  sort: int = pymongo.ASCENDING) -> List[GameEvent]:
        """

        Args:
            sort (): defines sort order 1 ascending -1 descending
            additional_filter (): query filter for the 'event' db
            start_end_day (): format 'YYYY-MM-DD'
            game_mode (): BR for Battle Royale, Arena for Arena
                (default is Both)
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

        event_list: list = self._get_event_dict(query_filter, sort)

        game_list: List[GameEvent] = []
        for game in event_list:
            game_event: GameEvent = GameEvent(**game)
            self.update_game_category_totals(game_event)
            self.update_game_mode(game_event)
            if game_mode and game_mode != game.game_mode:
                continue
            game_list.append(game_event)
        return game_list

    def get_ranked_games(self,
                         player_uid: int = 0,
                         season: Optional[Season] = None,
                         split_number: int = 0
                         ) -> List[GameEvent]:
        """
        Returns a list of 'filtered' games based on season / split (current if none given)
        Args:
            player_uid:  Player UID for ranked games (default all players)
            season: Season to get ranked games for
            split_number: Split number (cannot be zero of season given)

        Returns:
            List of all ranked game events
        """
        if not split_number:
            start_date = season.start_date
            end_date = season.end_date
        else:
            start_date, end_date = season.get_ranked_split_dates(split_number=split_number)

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
            start_end_day=(start_date, end_date),
            additional_filter=query_filter
        )

    def update_game_category_totals(self, game: GameEvent):
        """ Checks the game event to see if it has the category, and adds it """
        tracker: GameEventDetail
        for tracker in game.event:
            tracker_cat: str = self._tracker_info_collection.category_for_key(
                tracker.key
            )
            if hasattr(game, tracker_cat):
                setattr(game, tracker_cat, tracker.value)
        # Category not found

    def update_game_mode(self, game: GameEvent):
        """ Adds the Game Mode (BR, or Arena) to the game"""
        tracker: GameEventDetail
        for tracker in game.event:
            game.game_mode = self._tracker_info_collection.mode_for_key(
                tracker.key
            )

    def _get_event_dict(self, query_filter: dict, sort_order: int = 0) -> list:
        """ Query the DB for events based on filter """
        assert sort_order in (pymongo.ASCENDING, 0, pymongo.DESCENDING)
        if sort_order:
            return list(
                self._event_collection.find(query_filter).sort('timestamp', sort_order)
            )
        return list(self._event_collection.find(query_filter))

    def save_event_dict(self, event_data: dict):
        """ Saves any 'new' event data record """
        uid = event_data['uid']
        timestamp = event_data['timestamp']
        event_type = event_data['eventType']
        key = {"uid": uid, "timestamp": timestamp, "eventType": event_type}
        self._event_collection.update_one(
            filter=key, update={"$set": event_data}, upsert=True
        )

    def get_latest_game_timestamp(self, uid: str) -> int:
        """ returns the most recent timestamp """
        record = list(self._event_collection.find({'uid': uid}).sort([('timestamp', -1)]).limit(1))
        if len(record) == 1:
            return int(record[0]['timestamp'])
        return 0
