""" A collection of utilities so I don't repeat myself """
from typing import List
from apex_db_helper import ApexDBHelper
from models import Player

db_helper = ApexDBHelper()


def player_data_from_basic_player(basic_player_data: dict) -> Player:
    """ Returns a player dict from basic player data """
    global_info = basic_player_data.get('global')
    assert global_info
    realtime = basic_player_data.get('realtime')
    assert realtime
    battlepass_level = global_info['battlepass']['history'].get('season9')
    if battlepass_level is None:
        battlepass_level = -1
    player_data = {
        'name': global_info['name'],
        'uid': global_info['uid'],
        'platform': global_info['platform'],
        'level': global_info['level'],
        'is_online': realtime['isOnline'],
        'selected_legend': realtime['selectedLegend'],
        'battlepass_level': battlepass_level,
        'discord_id': 0
    }
    db_player = db_helper.get_tracked_player_by_uid(player_data['uid'])
    if db_player:
        player_data['discord_id'] = db_player.discord_id
    return Player.from_dict(player_data)


def players_sorted_by_key(tracked_players: List[Player], key: str):
    """ returns back a list of players sorted by the category """
    if key == 'name':
        sorted_players = sorted(
            tracked_players,
            key=lambda item: getattr(item, key).casefold()
        )
    else:
        sorted_players = sorted(
            tracked_players,
            key=lambda item: getattr(item, key), reverse=True
        )
    return sorted_players
