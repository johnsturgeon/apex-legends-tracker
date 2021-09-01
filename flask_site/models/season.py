""" Pydantic model for the 'season' collection """
from typing import Optional, Tuple, List

import arrow
from pydantic import BaseModel


# pylint: disable=missing-class-docstring
class SeasonInvalidSplitNumber(Exception):
    pass


class Season(BaseModel):
    start_date: str
    end_date: str
    season_number: int
    ranked_split_date: Optional[str] = None

    def dict(self, **kwargs):
        return super().dict(
            exclude_none=True,
            **kwargs
        )

    @property
    def first_ranked_split_dates(self) -> Tuple[str, str]:
        """
        Get the start_end dates for the first ranked split
        Returns:
            (start_date, end_date) formatted 'YYYY-MM-DD'
        """
        start_date = self.start_date
        end_date = arrow.get(self.ranked_split_date).shift(days=-1).format('YYYY-MM-DD')
        return start_date, end_date

    @property
    def second_ranked_split_dates(self) -> Tuple[str, str]:
        """
        Get the start_end dates for the second ranked split
        Returns:
            (start_date, end_date) formatted 'YYYY-MM-DD'
        """
        return self.ranked_split_date, self.end_date

    def get_ranked_split_dates(self, split_number: int) -> Tuple[str, str]:
        """
        Returns the ranked split dates for split number 1 or 2
        Args:
            split_number (): MUST be 1 or 2

        Returns:
            start_date, end_date
        """
        if split_number not in [1, 2]:
            raise SeasonInvalidSplitNumber
        if split_number == 1:
            return self.first_ranked_split_dates
        return self.second_ranked_split_dates


class SeasonCollection:
    def __init__(self, season_dict: dict):
        self.seasons: List[Season] = []
        for season in season_dict['seasons']:
            self.seasons.append(Season(**season))

    def get_current_season(self) -> Season:
        """ Returns the most recent 'season' """
        return self.seasons[-1]
