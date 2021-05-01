""" methods for retrieving and saving player data """
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
    for player in list_of_players:
        try:
            basic_player_data_list = apex_api_helper.api.basic_player_stats_by_uid(
                player['uid'], ALPlatform(value=player['platform']), skip_tracker_rank=True
            )
        except ALHTTPExceptionFromResponse:
            print(f"Player: {player} not found")
            continue
        assert isinstance(basic_player_data_list, list)
        assert len(basic_player_data_list) == 1
        player_data = basic_player_data_list[0]
        apex_db_helper.save_player_data(player_data=player_data)


def save_event_data(refresh_from_api: bool = False):
    """ Loop through all the players and save the event data """
    if refresh_from_api:
        list_of_players = apex_api_helper.get_tracked_players()
    else:
        list_of_players = apex_db_helper.get_tracked_players()
    for player in list_of_players:
        try:
            event_data_list = apex_api_helper.api.events_by_uid(
                uid=player['uid'], platform=ALPlatform(value=player['platform']), action=ALAction.GET
            )
        except ALHTTPExceptionFromResponse:
            print(f"Player: {player} not found")
            continue
        for event_data in event_data_list:
            apex_db_helper.save_event_data(event_data=event_data)


def add_player_by_name(player_name: str):
    """ adds a player to the API for tracking, then refresh the DB with that player """
    if player_name:
        pass
    # get uid
    # add uid to list
    # save player data refresh from api