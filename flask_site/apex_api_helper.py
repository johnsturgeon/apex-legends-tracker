""" A helper module for the apex legends API """
import os
from dotenv import load_dotenv
from apex_legends_api import ApexLegendsAPI, ALHTTPExceptionFromResponse, ALPlatform, ALAction
from apex_utilities import player_data_from_basic_player

load_dotenv()

# pylint disable=too-few-public-methods
class ApexAPIHelper:  # noqa R0903
    """ Wrapper class for the Apex API to add a few helper methods """
    def __init__(self):
        self.api: ApexLegendsAPI = ApexLegendsAPI(api_key=os.getenv('APEX_LEGENDS_API_KEY'))

    def get_tracked_players(self) -> list:
        """ Return a list of dictionaries containing each player's data"""
        player_dict: dict = dict()
        # This is the 'events' api, but it does indeed return back a list of players by UID
        player_list = self.api.events('GoshDarnedHero', ALPlatform.PC, ALAction.INFO)
        for player in player_list[0]['data']:
            try:
                basic_stats = self.api.basic_player_stats_by_uid(
                    uid=player['uid'], platform=ALPlatform(value=player['platform'])
                )
            except ALHTTPExceptionFromResponse:
                continue
            player_dict[player['uid']] = player_data_from_basic_player(basic_stats[0])

        return list(player_dict.values())
