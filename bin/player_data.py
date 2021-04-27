""" methods for retrieving and saving player data """
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_legends_api import ALPlatform, ALAction

apex_api_helper = ApexAPIHelper()
apex_db_helper = ApexDBHelper()


def save_player_data():
    """ Loop through all players and save the data """
    for player in apex_db_helper.get_tracked_players():
        basic_player_data_list = apex_api_helper.api.basic_player_stats_by_uid(
            player['uid'], ALPlatform(value=player['platform']), skip_tracker_rank=True
        )
        assert isinstance(basic_player_data_list, list)
        assert len(basic_player_data_list) == 1
        player_data = basic_player_data_list[0]
        apex_db_helper.save_player_data(player_data=player_data)


def save_event_data():
    """ Loop through all the players and save the event data """
    for player in apex_db_helper.get_tracked_players():
        event_data_list = apex_api_helper.api.events_by_uid(
            uid=player['uid'], platform=ALPlatform(value=player['platform']), action=ALAction.GET
        )
        for event_data in event_data_list:
            apex_db_helper.save_event_data(event_data=event_data)
