""" basic info model tests """
from models import Config, RankedDivisionInfo


# pylint: disable=missing-function-docstring
def test_from_dict(config_dict):
    config_object: Config = Config(**config_dict)
    assert config_object.battlepass_goal == 100


def test_ranked_division_info(config_dict):
    config_object: Config = Config(**config_dict)
    ranked_division_info: RankedDivisionInfo = config_object.ranked_division_info
    assert len(ranked_division_info.divisions) == 5
    assert len(ranked_division_info.tiers) == 4
    for tier in ranked_division_info.tiers:
        assert tier in ['I', 'II', 'III', 'IV']
    for division in ranked_division_info.divisions:
        assert division.name in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
        assert 300 <= division.rp_between_tiers <= 700


def test_to_dict(config_dict):
    apex_info_object: Config = Config(**config_dict)
    del config_dict['_id']
    apex_info_object_to_dict: dict = apex_info_object.dict()
    assert apex_info_object_to_dict == config_dict
