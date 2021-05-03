""" A helper module for the apex legends API """
import os
from dotenv import load_dotenv
from apex_legends_api import ApexLegendsAPI, ALPlatform, ALAction

load_dotenv()

# pylint disable=too-few-public-methods
class ApexAPIHelper:  # noqa R0903
    """ Wrapper class for the Apex API to add a few helper methods """
    def __init__(self):
        self.api: ApexLegendsAPI = ApexLegendsAPI(api_key=os.getenv('APEX_LEGENDS_API_KEY'))

    def get_tracked_players(self) -> list:
        """ Return a list of dictionaries containing each player's data"""
        player_dict: dict = dict()
        player_list = self.api.events('GoshDarnedHero', ALPlatform.PC, ALAction.INFO)
        for player in player_list[0]['data']:
            player_dict[player['uid']] = {
                'uid': int(player['uid']),
                'name': '',
                'platform': player['platform']
            }

        return list(player_dict.values())
