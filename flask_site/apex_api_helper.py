""" A helper module for the apex legends API """
import os
from typing import List, Optional

import httpx
from apex_legends_api import ApexLegendsAPI, ALHTTPExceptionFromResponse, ALPlatform, ALAction

from httpx import AsyncClient, Response, ReadTimeout, ConnectTimeout

# pylint: disable=import-error
from instance.config import get_config
config = get_config(os.getenv('FLASK_ENV'))


class RespawnSlowDownException(Exception):
    """ A wrapper class for when respawn wants us to slow down """


class ApexAPIHelper:
    """ Wrapper class for the Apex API to add a few helper methods """
    def __init__(self):
        self.api: ApexLegendsAPI = ApexLegendsAPI(api_key=config.APEX_LEGENDS_API_KEY)

    @property
    def basic_players_from_api(self) -> List[dict]:
        """ Return a list of dictionaries containing each player's data"""
        list_of_players: list = []
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

    @staticmethod
    async def get_stryder_data(player_uid: int, platform: str) -> Optional[dict]:
        """ Get the raw CDATA json response from Respawn """
        headers = {'User-Agent': 'Respawn HTTPS/1.0'}

        url: str = config.STRYDER_URL
        params: dict = {
            'qt': 'user-getinfo',
            'getinfo': 1,
            'json': 1,
            'uid': player_uid,
            'hardware': platform
        }
        client: AsyncClient
        async with httpx.AsyncClient(headers=headers, params=params, timeout=10) as client:
            try:
                response: Response = await client.get(url)
            except (ReadTimeout, ConnectTimeout) as timeout_error:
                logger = config.logger(os.path.basename(__file__))
                logger.warning(
                    "Timeout fetching respawn data for %s-- continuing: %s", player_uid,
                    timeout_error
                )
                return None
            if response.status_code == 200:
                response_text = response.json()
            elif response.status_code == 429:
                logger = config.logger(os.path.basename(__file__))
                logger.error("SLOW DOWN from respawn (detail to follow)")
                logger.error(response)
                logger.error(response.headers)
                raise RespawnSlowDownException(response)
            else:
                raise ALHTTPExceptionFromResponse(response)

        return response_text
