""" A helper module for the apex legends API """
import os
from typing import List

from apex_legends_api import ApexLegendsAPI, ALHTTPExceptionFromResponse, ALPlatform, ALAction

# pylint: disable=import-error
from instance.config import get_config
config = get_config(os.getenv('FLASK_ENV'))


class ApexAPIHelper:
    """ Wrapper class for the Apex API to add a few helper methods """
    def __init__(self):
        self.api: ApexLegendsAPI = ApexLegendsAPI(api_key=config.APEX_LEGENDS_API_KEY)

    @property
    def basic_players_from_api(self) -> List[dict]:
        """ Return a list of dictionaries containing each player's data"""
        list_of_players: list = list()
        # This is the 'events' api, but it does indeed return back a list of players by UID
        player_list = self.api.events('GoshDarnedHero', ALPlatform.PC, ALAction.INFO)
        for player in player_list[0]['data']:
            try:
                basic_player = self.api.basic_player_stats_by_uid(
                    uid=player['uid'], platform=ALPlatform(value=player['platform'])
                )
            except ALHTTPExceptionFromResponse:
                continue
            assert len(basic_player) == 1
            list_of_players.append(basic_player[0])

        return list_of_players
