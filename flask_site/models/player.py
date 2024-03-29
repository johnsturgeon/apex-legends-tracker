""" Dataclass to represent player collection """
from typing import Optional, List, Any

import pymongo.database

from pydantic import BaseModel


class BadDictException(Exception):
    """ Custom error message raised when I get a bad dictionary """
    def __init__(self, bad_dict: Any, message: str = None) -> None:
        self.bad_dictionary = str(bad_dict)
        self.message = message
        super().__init__(message)


# pylint: disable=too-many-instance-attributes
class Player(BaseModel):
    """ Player data class """
    uid: int
    is_online: int
    name: str
    platform: str
    selected_legend: str
    level: int
    battlepass_level: int
    discord_id: int
    clan: str
    games_played: Optional[int] = None
    kills_avg: Optional[float] = None
    kills_total: Optional[int] = None
    wins: Optional[int] = None
    damage_avg: Optional[float] = None
    damage_total: Optional[int] = None
    xp_total: Optional[int] = None
    point_total: Optional[int] = None
    minute_total: Optional[int] = None

    def dict(self, **kwargs):
        return super().dict(
            exclude_none=True,
            **kwargs
        )


class PlayerCollection:
    """ Player Collection class """
    def __init__(self, database: pymongo.database.Database):
        self._collection = database.player

    def get_tracked_players(self) -> list[Player]:
        """ Return a list of dictionaries containing each player's data"""
        player_list: List[Player] = []
        for player_data in self._collection.find():
            player_list.append(Player(**player_data))
        return player_list

    def get_tracked_player_by_uid(self, uid: int) -> Optional[Player]:
        """ Returns one player given a uid """
        player_data = self._collection.find_one(
            filter={'uid': uid}
        )
        if player_data:
            return Player(**player_data)
        return None

    def get_player_by_discord_id(self, discord_id: int) -> Optional[Player]:
        """ Returns one `Player` given a discord id / None if no match"""
        player_dict: dict = self._collection.find_one({'discord_id': discord_id})
        if player_dict:
            return Player(**player_dict)
        return None

    def save_player(self, player: Player):
        """ Saves player to database """
        key = {'uid': player.uid}
        self._collection.update_one(
            filter=key,
            update={"$set": player.dict()},
            upsert=True
        )

    def player_data_from_basic_player(self, basic_player_data: dict) -> Player:
        """ Returns a player dict from basic player data """
        global_info = basic_player_data.get('global')
        if not global_info:
            raise BadDictException(
                bad_dict=basic_player_data,
                message="Expected Global Info in dictionary")
        realtime = basic_player_data.get('realtime')
        if not realtime:
            raise BadDictException(
                bad_dict=basic_player_data,
                message="Expected RealTime in dictionary"
            )
        assert realtime
        battlepass_level = global_info['battlepass']['history'].get('season10')
        if battlepass_level is None:
            battlepass_level = -1
        player_data = {
            'name': global_info['name'],
            'uid': global_info['uid'],
            'platform': global_info['platform'],
            'level': global_info['level'],
            'is_online': realtime['isOnline'],
            'selected_legend': realtime['selectedLegend'],
            'battlepass_level': battlepass_level,
            'discord_id': 0,
            'clan': 'NOT_SET'
        }
        db_player = self.get_tracked_player_by_uid(player_data['uid'])
        if db_player:
            player_data['discord_id'] = db_player.discord_id
            player_data['clan'] = db_player.clan
        return Player(**player_data)
