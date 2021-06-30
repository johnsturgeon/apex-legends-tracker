""" methods for retrieving and saving player data """
import os
from threading import Thread
from typing import List

from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_legends_api import ALPlatform, ALAction, ALHTTPExceptionFromResponse

from models import Player
# pylint: disable=import-error
from instance.config import get_config
config = get_config(os.getenv('FLASK_ENV'))

apex_api_helper = ApexAPIHelper()
apex_db_helper = ApexDBHelper()
logger = config.logger(os.path.basename(__file__))


def save_all_player_data():
    """ Loop through all players and save the data """
    list_of_players = apex_db_helper.player_collection.get_tracked_players()
    thread_method_with_player(save_one_player_data, list_of_players)
    thread_method_with_player(save_one_player_event_data, list_of_players)


def thread_method_with_player(method_name, list_of_players: List[Player]):
    """ Executes a method name on a list of players (threaded) """
    threads: list = []
    for player in list_of_players:
        threaded_method = Thread(target=method_name, args=(player,))
        threads.append(threaded_method)
    thread: Thread
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def save_one_player_data(player: Player):
    """ Saves one player's data if it has been updated """
    try:
        basic_player_data_list = apex_api_helper.api.basic_player_stats_by_uid(
            str(player.uid), ALPlatform(value=player.platform)
        )
    except ALHTTPExceptionFromResponse:
        logger.warning("Player: %s not found", player)
        return
    except ConnectionError as con_error:
        logger.warning("Connection Error Saving 'player data'.\nError message: %s", con_error)
        return
    else:
        if not isinstance(basic_player_data_list, list):
            logger.warning(
                "basic_player_data_list is not a list, here's what we got: %s",
                basic_player_data_list
            )
            return
        if not len(basic_player_data_list) == 1:
            logger.warning(
                "basic_player_data_list is not just one, here's what it is: %s",
                basic_player_data_list
            )
            return
        basic_player_data = basic_player_data_list[0]
        logger.debug("Saving Basic Player Data: %s", basic_player_data)
        apex_db_helper.save_basic_player_data(player_data=basic_player_data)
        player = apex_db_helper.player_collection.player_data_from_basic_player(basic_player_data)
        apex_db_helper.player_collection.save_player(player)


def save_one_player_event_data(player: Player):
    """ saves just one player's event data """
    try:
        logger.debug("Getting events by UID for player: %s: ", player)
        event_data_list = apex_api_helper.api.events_by_uid(
            uid=str(player.uid),
            platform=ALPlatform(value=player.platform),
            action=ALAction.GET
        )
        logger.debug("Got events by UID for player %s ", player)
    except ALHTTPExceptionFromResponse:
        logger.warning("Player: %s not found", player)
        return
    except ConnectionError as con_error:
        logger.warning("Connection Error Saving 'event'.\nError message: %s", con_error)
        return
    else:
        for event_data in event_data_list:
            logger.debug("Saving Player %s Data: %s", player, event_data)
            apex_db_helper.event_collection.save_event_dict(event_data=event_data)


def update_player_collection_from_api():
    """ Pulls current players from the API and populates their data from the api and updates
    the player DB """
    tracked_players = apex_api_helper.basic_players_from_api
    player_data: dict
    for player_data in tracked_players:
        player: Player = apex_db_helper.player_collection.player_data_from_basic_player(player_data)
        apex_db_helper.player_collection.save_player(player=player)


def is_anyone_online() -> bool:
    """ Returns TRUE if any player is currently online """
    player: Player
    for player in apex_db_helper.player_collection.get_tracked_players():
        if player.is_online:
            return True
    return False


if __name__ == "__main__":
    update_player_collection_from_api()
    # apex_db_helper.event_collection.delete_many({'eventType': 'rankScoreChange'})
