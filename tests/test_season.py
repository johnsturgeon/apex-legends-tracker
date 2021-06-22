""" Season Model tests """
from typing import List

import pytest

from models.season import Season, SeasonInvalidSplitNumber


# pylint: disable=missing-function-docstring
def test_from_dict(season_list: List[dict]):
    for season_dict in season_list:
        season_object: Season = Season(**season_dict)
        assert isinstance(season_object, Season)


def test_dates(season_list: List[dict]):
    for season_dict in season_list:
        season_object: Season = Season(**season_dict)
        assert season_object.start_date < season_object.end_date
        if season_object.ranked_split_date:
            assert season_object.start_date <= \
                   season_object.ranked_split_date <= \
                   season_object.end_date


def test_to_dict(season_list: List[dict]):
    for season_dict in season_list:
        season_object: Season = Season(**season_dict)
        del season_dict['_id']
        season_object_to_dict: dict = season_object.dict()
        assert season_object_to_dict == season_dict


def test_get_ranked_split_dates(season_list: List[dict]):
    current_season: Season = Season(**season_list[-1])
    with pytest.raises(SeasonInvalidSplitNumber):
        current_season.get_ranked_split_dates(split_number=0)
    with pytest.raises(SeasonInvalidSplitNumber):
        current_season.get_ranked_split_dates(split_number=3)

    start_date, end_date = current_season.get_ranked_split_dates(split_number=1)
    assert start_date < end_date
    assert start_date == current_season.start_date
    assert start_date == '2021-05-04'
    assert end_date == '2021-06-14'
    start_date, end_date = current_season.get_ranked_split_dates(split_number=2)
    assert start_date < end_date
    assert end_date == current_season.end_date
    assert start_date == current_season.ranked_split_date
    assert start_date == '2021-06-15'
