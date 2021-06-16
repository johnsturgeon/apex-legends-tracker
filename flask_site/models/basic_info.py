""" Dataclass to represent basic_info collection """
from dataclasses import dataclass
from typing import List, Optional

from pymongo.collection import Collection
from mashumaro import DataClassDictMixin


# pylint: disable=missing-class-docstring
@dataclass
class RankTier(DataClassDictMixin):
    division: str
    tier: str
    distance_to_next: int


@dataclass
class Division(DataClassDictMixin):
    name: str
    color: str
    rp_between_tiers: int


@dataclass
class RankedDivisionInfo(DataClassDictMixin):
    divisions: List[Division]
    tiers: List[str]


@dataclass
class RankedSplit(DataClassDictMixin):
    split_number: int
    end_date: str
    start_date: str


@dataclass
class BattlepassInfo(DataClassDictMixin):
    start_date: str
    end_date: str
    max_battlepass: int
    goal_battlepass: int


@dataclass
class Season(DataClassDictMixin):
    season_number: int
    ranked_splits: List[RankedSplit]
    battlepass_info: BattlepassInfo


@dataclass
class BasicInfo(DataClassDictMixin):
    current_split: int
    current_season: int
    seasons: List[Season]
    ranked_division_info: RankedDivisionInfo

    def get_ranked_splits(self, season_number: int = 0) -> List[RankedSplit]:
        """ Returns the ranked split for given season / split (current if 0) """
        current_season: Season = self.get_season(season_number)
        if current_season.ranked_splits:
            return current_season.ranked_splits
        return []

    def get_season(self, season_number: int = 0) -> Season:
        """ Returns the info for the given season (current season if 0) """
        season_index = (season_number if season_number else self.current_season) - 1
        return self.seasons[season_index]

    def get_rank_div_tier(self, rank_points: int) -> Optional[RankTier]:
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

    def get_season_start_day(self, season_number: int = 0) -> str:
        """ Returns the start date of the season """
        season = self.get_season(season_number)
        if len(season.ranked_splits) > 0:
            return season.ranked_splits[0].start_date
        return ""

    def get_season_end_day(self, season_number: int = 0) -> str:
        """ Returns the start date of the season """
        season = self.get_season(season_number)
        if len(season.ranked_splits) > 0:
            return season.ranked_splits[-1].end_date
        return ""


class BasicInfoCollection:
    """ Collection class for the 'basic_info' collection """
    def __init__(self, collection: Collection):
        self._collection = collection
        self._basic_info: Optional[BasicInfo] = None

    @property
    def basic_info(self) -> BasicInfo:
        """ Factory method for BasicInfo data """
        if not self._basic_info:
            self._basic_info = BasicInfo.from_dict(self._collection.find_one({}))
        return self._basic_info
