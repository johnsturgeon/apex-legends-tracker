""" configure test fixtures """
import os
import json
import pytest


def get_full_filepath(test_filename):
    """ return a fully qualified file location for the test file"""
    file_path = os.path.dirname(os.path.abspath(__file__))
    return_filepath = os.path.abspath(file_path + "/json/" + test_filename)
    return return_filepath


# pylint: disable=missing-function-docstring
@pytest.fixture()
def event_list():
    with open(get_full_filepath('event.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def game_event_list():
    with open(get_full_filepath('game_event.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def level_event_list():
    with open(get_full_filepath('level_event.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def rank_event_list():
    with open(get_full_filepath('rank_event.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def session_event_list():
    with open(get_full_filepath('session_event.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def season_list():
    with open(get_full_filepath('season.json')) as json_file:
        yield json.load(json_file)


@pytest.fixture()
def config_dict():
    with open(get_full_filepath('config.json')) as json_file:
        yield json.load(json_file)
