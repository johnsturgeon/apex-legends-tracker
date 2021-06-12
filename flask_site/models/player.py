""" Dataclass to represent player collection """
from dataclasses import dataclass
from typing import Optional, List
from pymongo.collection import Collection


from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig, TO_DICT_ADD_OMIT_NONE_FLAG


# pylint: disable=too-many-instance-attributes
@dataclass
class Player(DataClassDictMixin):
    """ Player data class """
    uid: int
    is_online: int
    name: str
    platform: str
    selected_legend: str
    level: int
    battlepass_level: int
    discord_id: int
    games_played: Optional[int] = None
    kill_avg: Optional[float] = None
    wins: Optional[int] = None
    damage_avg: Optional[float] = None

    class Config(BaseConfig):
        """ Config class """
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]


class PlayerCollection:
    """ Player Collection class """
    def __init__(self, collection: Collection):
        self._collection = collection

    def get_tracked_players(self) -> list[Player]:
        """ Return a list of dictionaries containing each player's data"""
        player_list: List[Player] = list()
        for player_data in self._collection.find():
            player_list.append(Player.from_dict(player_data))
        return player_list

    def get_tracked_player_by_uid(self, uid: int) -> Player:
        """ Returns one player given a uid """
        player_data = self._collection.find_one(
            filter={'uid': uid}
        )
        return Player.from_dict(player_data)

    def get_player_by_discord_id(self, discord_id: int) -> Optional[Player]:
        """ Returns one `Player` given a discord id / None if no match"""
        player_dict: dict = self._collection.find_one({'discord_id': discord_id})
        if player_dict:
            return Player.from_dict(player_dict)
        return None

    def save_player(self, player: Player):
        """ Saves player to database """
        key = {'uid': player.uid}
        self._collection.update_one(
            filter=key,
            update={"$set": player.to_dict(omit_none=True)},
            upsert=True
        )

    def player_data_from_basic_player(self, basic_player_data: dict) -> Player:
        """ Returns a player dict from basic player data """
        global_info = basic_player_data.get('global')
        assert global_info
        realtime = basic_player_data.get('realtime')
        assert realtime
        battlepass_level = global_info['battlepass']['history'].get('season9')
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
            'discord_id': 0
        }
        db_player = self.get_tracked_player_by_uid(player_data['uid'])
        if db_player:
            player_data['discord_id'] = db_player.discord_id
        return Player.from_dict(player_data)
