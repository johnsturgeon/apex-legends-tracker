"""
Contains all the domain level classes for abstracting the ALPlayer class from apex legends api
"""
from apex_legends_api import ApexLegendsAPI, ALPlayer
from apex_legends_api.al_domain import Event, GameEvent
from apex_legends_api.al_base import ALEventType


class PlayerTracker:
    """ Tracker wrapper for the ALPlayer class """
    def __init__(self, player: ALPlayer):
        self.al_player: ALPlayer = player
        """ Apex Legends player class """

    def game_events(self) -> list[GameEvent]:
        game_events: list[GameEvent]
        for event in self.al_player.events:
            if isinstance(event.event_type, GameEvent):
                game_events.append(event)
        return game_events

    def day_totals(self):
        for game_event in self.game_events():
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

