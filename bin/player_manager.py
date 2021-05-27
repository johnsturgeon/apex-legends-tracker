""" methods for retrieving and saving player data """
from threading import Thread
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_utilities import player_data_from_basic_player
from apex_legends_api import ALPlatform, ALAction, ALHTTPExceptionFromResponse

apex_api_helper = ApexAPIHelper()
apex_db_helper = ApexDBHelper()
log = apex_db_helper.logger


def save_player_data():
    """ Loop through all players and save the data """
    list_of_players = apex_db_helper.get_tracked_players()
    thread_method_with_player(save_one_player_data, list_of_players)
    thread_method_with_player(save_one_player_event_data, list_of_players)


def thread_method_with_player(method_name, list_of_players):
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


def save_one_player_data(player: dict):
    """ Saves one player's data if it has been updated """
    try:
        basic_player_data_list = apex_api_helper.api.basic_player_stats_by_uid(
            player['uid'], ALPlatform(value=player['platform'])
        )
    except ALHTTPExceptionFromResponse:
        log.warning("Player: %s not found", player)
        return
    else:
        assert isinstance(basic_player_data_list, list)
        assert len(basic_player_data_list) == 1
        basic_player_data = basic_player_data_list[0]
        log.debug("Saving Basic Player Data: %s", basic_player_data)
        apex_db_helper.save_basic_player_data(player_data=basic_player_data)
        player_data = player_data_from_basic_player(basic_player_data)
        apex_db_helper.save_player_data(player_data=player_data)


def save_one_player_event_data(player: dict):
    """ saves just one player's event data """
    try:
        log.debug("Getting events by UID for player: %s: ", player)
        event_data_list = apex_api_helper.api.events_by_uid(
            uid=player['uid'],
            platform=ALPlatform(value=player['platform']),
            action=ALAction.GET
        )
        log.debug("Got events by UID for player %s ", player)
    except ALHTTPExceptionFromResponse:
        log.warning("Player: %s not found", player)
        return
    else:
        for event_data in event_data_list:
            log.debug("Saving Player %s Data: %s", player, event_data)
            apex_db_helper.save_event_data(event_data=event_data)


def update_player_collection_from_api():
    """ Pulls current players from the API and populates their data from the api and updates
    the player DB """
    tracked_players = apex_api_helper.get_tracked_players()
    for player in tracked_players:
        apex_db_helper.save_player_data(player_data=player)


def is_anyone_online() -> bool:
    """ Returns TRUE if any player is currently online """
    for player in apex_db_helper.get_tracked_players():
        if player['is_online']:
            return True
    return False


if __name__ == "__main__":
    update_player_collection_from_api()
