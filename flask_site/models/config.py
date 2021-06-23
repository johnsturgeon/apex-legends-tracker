""" Data model for the apex_info collection """
from typing import List, Optional

import pymongo.database
from pydantic import BaseModel


# pylint: disable=missing-class-docstring
class RankTier(BaseModel):
    division: str
    tier: str
    distance_to_next: int


class Division(BaseModel):
    name: str
    color: str
    rp_between_tiers: int


class RankedDivisionInfo(BaseModel):
    divisions: List[Division]
    tiers: List[str]


class Config(BaseModel):
    ranked_division_info: RankedDivisionInfo
    battlepass_goal: int

    def get_rank_div_tier_for_points(self, rank_points: int) -> Optional[RankTier]:
        """
        Get the RankTier for a given score
        Args:
            rank_points (): Ranking Points

        Returns:
            RankTier (i.e. 'Platinum', 'IV')

        """
        lower_rp: int = 0
        for division in self.ranked_division_info.divisions:
            tier_index = 1
            for tier in self.ranked_division_info.tiers:
                upper_rp = lower_rp + division.rp_between_tiers
                if rank_points in range(lower_rp, upper_rp):
                    to_next = upper_rp - rank_points
                    return RankTier(tier=tier, division=division.name, distance_to_next=to_next)
                tier_index += 1
                lower_rp = upper_rp

        return None


class ConfigCollection:
    """ Collection class for the 'basic_info' collection """
    def __init__(self, config_dict: dict):
        self.config: Config = Config(**config_dict)
