""" Dataclass to represent player collection """
from dataclasses import dataclass
from typing import Optional

# pylint: disable=too-many-instance-attributes
from mashumaro import DataClassDictMixin


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
