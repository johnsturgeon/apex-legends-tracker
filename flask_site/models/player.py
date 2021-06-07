""" Dataclass to represent player collection """
from dataclasses import dataclass
from typing import Optional

# pylint: disable=too-many-instance-attributes
from mashumaro import DataClassDictMixin
from mashumaro.config import BaseConfig, TO_DICT_ADD_OMIT_NONE_FLAG


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
    games_played: Optional[int] = None
    kill_avg: Optional[float] = None
    wins: Optional[int] = None
    damage_avg: Optional[float] = None

    class Config(BaseConfig):
        """ Config class """
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]
