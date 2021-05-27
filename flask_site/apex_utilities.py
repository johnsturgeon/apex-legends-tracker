""" A collection of utilities so I don't repeat myself """


def player_data_from_basic_player(basic_player_data):
    """ Returns a player dict from basic player data """
    global_info = basic_player_data.get('global')
    assert global_info
    realtime = basic_player_data.get('realtime')
    assert realtime
    return {
        'name': global_info['name'],
        'uid': global_info['uid'],
        'platform': global_info['platform'],
        'level': global_info['level'],
        'is_online': realtime['isOnline'],
        'selected_legend': realtime['selectedLegend']
    }
