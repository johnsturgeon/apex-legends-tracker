""" Dataclass to represent basic_info collection """
from dataclasses import dataclass
from typing import List, Optional


# pylint: disable=missing-class-docstring
@dataclass
class RankTier:
    division: str
    tier: str


@dataclass
class Division:
    name: str
    color: str
    rp_between_tiers: int


@dataclass
class RankedDivisionInfo:
    divisions: List[Division]
    tiers: List[str]


@dataclass
class RankedSplit:
    split_number: int
    end_date: str
    start_date: str


@dataclass
class BattlepassInfo:
    start_date: str
    end_date: str
    max_battlepass: int
    goal_battlepass: int


@dataclass
class Season:
    season_number: int
    ranked_splits: List[RankedSplit]
    battlepass_info: BattlepassInfo


@dataclass
class BasicInfo:
    current_split: int
    current_season: int
    seasons: List[Season]
    ranked_division_info: RankedDivisionInfo

    def get_ranked_split(self, season_number: int = 0, split_number: int = 0) -> RankedSplit:
        """ Returns the ranked split for given season / split (current if 0) """
        current_season: Season = self.get_season(season_number)
        split_index = (split_number if split_number else self.current_split) - 1
        return current_season.ranked_splits[split_index]

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
                    return RankTier(tier=tier, division=division.name)
                tier_index += 1
                lower_rp = upper_rp

        return None
