""" methods for retrieving and saving player data """
from threading import Thread
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_legends_api import ALPlatform, ALAction, ALHTTPExceptionFromResponse

apex_api_helper = ApexAPIHelper()
apex_db_helper = ApexDBHelper()


def save_player_data(refresh_from_api: bool = False):
    """ Loop through all players and save the data """
    if refresh_from_api:
        list_of_players = apex_api_helper.get_tracked_players()
    else:
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
            player['uid'], ALPlatform(value=player['platform']), skip_tracker_rank=True
        )
    except ALHTTPExceptionFromResponse:
        print(f"Player: {player} not found")
        return
    else:
        assert isinstance(basic_player_data_list, list)
        assert len(basic_player_data_list) == 1
        player_data = basic_player_data_list[0]
        apex_db_helper.save_basic_player_data(player_data=player_data)


def save_one_player_event_data(player: dict):
    """ saves just one player's event data """
    try:
        event_data_list = apex_api_helper.api.events_by_uid(
            uid=player['uid'],
            platform=ALPlatform(value=player['platform']),
            action=ALAction.GET
        )
    except ALHTTPExceptionFromResponse:
        print(f"Player: {player} not found")
        return
    else:
        for event_data in event_data_list:
            latest_timestamp = apex_db_helper.get_latest_event_timestamp()
            if event_data['timestamp'] > latest_timestamp:
                apex_db_helper.save_event_data(event_data=event_data)


def add_player_by_name(player_name: str, platform: ALPlatform):
    """ adds a player to the API for tracking, then refresh the DB with that player """
    uid = apex_api_helper.api.nametouid(player=player_name, platform=platform)
    apex_api_helper.api.add_player_by_uid(uid, platform)
    save_player_data(refresh_from_api=True)


def is_anyone_online() -> bool:
    """ Returns TRUE if any player is currently online """
    for player in apex_db_helper.get_tracked_players(active_only=True):
        if player['is_online']:
            return True
    return False


def update_player_collection():
    """ Updated the player collection """
    for player in apex_db_helper.get_tracked_players(active_only=True):
        player['active'] = True
        apex_db_helper.save_player_data(player)


if __name__ == "__main__":
    update_player_collection()
