""" Dataclass to represent player collection """
from __future__ import annotations

from typing import Tuple

import pymongo.database
from pydantic import BaseModel, Field

from instance.config import get_config
config = get_config('development')


class PlayerNotFoundException(Exception):
    """ Simple exception for when a player is not found """


def key_value_for_cdata(cdata: str) -> Tuple[str, str]:
    """ returns the key, value pair for a given CDATA key """
    if isinstance(cdata, int):
        cdata = str(cdata)
    # cdata_map = load_data('cdata_map.json')
    # if cdata_map.get(cdata):
    #     return tuple(cdata_map[cdata])
    return 'unknown', cdata


# pylint: disable=missing-class-docstring
class RespawnRecord(BaseModel):
    timestamp: int
    uid: int
    hardware: str
    name: str
    # kills: int
    # wins: int
    # matches: int
    ban_reason: int = Field(alias='banReason')
    ban_seconds: int = Field(alias='banSeconds')
    # elite_streak: int = Field(alias='eliteStreak')
    rank_score: int = Field(alias='rankScore')
    arena_score: int = Field(alias='arenaScore')
    # char_ver: int = Field(alias='charVer')
    # char_idx: int = Field(alias='charIdx')
    # privacy: str
    # version: int = Field(alias='cdata0')
    # unused01: int = Field(alias='cdata1')
    character: int = Field(alias='cdata2')
    character_skin: int = Field(alias='cdata3')
    banner_frame: int = Field(alias='cdata4')
    banner_stance: int = Field(alias='cdata5')
    banner_badge1: int = Field(alias='cdata6')
    banner_badge1_tier: int = Field(alias='cdata7')
    banner_badge2: int = Field(alias='cdata8')
    banner_badge2_tier: int = Field(alias='cdata9')
    banner_badge3: int = Field(alias='cdata10')
    banner_badge3_tier: int = Field(alias='cdata11')
    banner_tracker1: int = Field(alias='cdata12')
    banner_tracker1_value: int = Field(alias='cdata13')
    banner_tracker2: int = Field(alias='cdata14')
    banner_tracker2_value: int = Field(alias='cdata15')
    banner_tracker3: int = Field(alias='cdata16')
    banner_tracker3_value: int = Field(alias='cdata17')
    character_intro_quip: int = Field(alias='cdata18')
    # unused19: int = Field(alias='cdata19')
    # unused20: int = Field(alias='cdata20')
    # unused21: int = Field(alias='cdata21')
    # unused22: int = Field(alias='cdata22')
    account_level: int = Field(alias='cdata23')
    account_progress_int: int = Field(alias='cdata24')
    # unused25: int = Field(alias='cdata25')
    # unused26: int = Field(alias='cdata26')
    # unused27: int = Field(alias='cdata27')
    # unused28: int = Field(alias='cdata28')
    # unused29: int = Field(alias='cdata29')
    # unused30: int = Field(alias='cdata30')
    player_in_match: int = Field(alias='cdata31')
    online: int
    joinable: int
    party_full: int = Field(alias='partyFull')
    party_in_match: int = Field(alias='partyInMatch')
    # time_since_server_change: int = Field(alias='timeSinceServerChange')
    # endpoint: str
    # communities: Dict[str, Any]

    # @validator(
    #     'character',
    #     'character_skin',
    #     'banner_frame',
    #     'banner_stance',
    #     'banner_badge1',
    #     'banner_badge2',
    #     'banner_badge3',
    #     'banner_tracker1',
    #     'banner_tracker2',
    #     'banner_tracker3',
    #     'character_intro_quip'
    # )
    # def validate_cdata(cls, v):
    #     _, value = key_value_for_cdata(v)
    #     return value


class RespawnCollection:
    def __init__(self, db: pymongo.database.Database):
        self._respawn_collection: pymongo.collection.Collection = db.respawn_record

    def save_respawn_record(self, obj: RespawnRecord):
        """ Saves one record to the respawn DB"""
        self._respawn_collection.insert_one(obj.dict())
