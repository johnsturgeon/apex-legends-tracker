""" Initial tracker script for update the Mongo DB """
# from pymongo import MongoClient
from apex_legends_api import ApexLegendsAPI, ALPlayer, ALPlatform
from apex_legends_api.al_base import print_description, ALEventType
from apex_legends_api.al_domain import GameEvent, DataTracker
import arrow
# from player_db import PlayerDB
# from session_db import SessionDB
# from pymongo.collection import Collection
import common_init


def main():
    """ main method run from CLI """
    settings = common_init.get_settings()
    # mongo_user = settings['mongo_user'].get('value')
    # mongo_password = settings['mongo_password'].get('value')
    # mongo_hostname = settings['mongo_hostname'].get('value')
    # mongo_port = settings['mongo_port'].get('value')
    # mongo_auth_db = settings['mongo_auth_db'].get('value')
    # mongo_uri = \
    #     f"mongodb://{mongo_user}:{mongo_password}@{mongo_hostname}:{mongo_port}/{mongo_auth_db}"
    # mongo_db: MongoClient = MongoClient(mongo_uri)

    # player_collection: Collection = mongo_db.apex_legends.player
    # session_collection: Collection = mongo_db.apex_legends.player_sessions

    tracker_api_key = settings['tracker_api_key'].get('value')

    apex_api: ApexLegendsAPI = ApexLegendsAPI(tracker_api_key)
    player: ALPlayer = apex_api.get_player(name='GoshDarnedHero', platform=ALPlatform.PC)
    damage_day: dict = dict()
    game_day: dict = dict()
    for match in player.events:
        if match.event_type == ALEventType.GAME:
            match.__class__ = GameEvent
            day_key = str(arrow.get(match.timestamp).to('US/Pacific').floor('day'))
            if day_key not in damage_day:
                damage_day[day_key] = 0
                game_day[day_key] = 0
            tracker: DataTracker
            found_damage_tracker = False
            for tracker in match.game_data_trackers:
                if tracker.key == 'damage' or tracker.key == 'specialEvent_damage':
                    found_damage_tracker = True
                    damage_day[day_key] += int(tracker.value)
                    game_day[day_key] += 1
            if not found_damage_tracker:
                print("No Damage Tracker for " + match.legend_played)
                print_description(match)

    for key in damage_day:
        print("day: " + key)
        print("Damage: " + str(damage_day[key]))
        print("Games: " + str(game_day[key]))
        print("Damage / Game: " + str(int((damage_day[key] / game_day[key]))))


if __name__ == "__main__":
    main()
