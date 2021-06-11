""" A collection of utilities so I don't repeat myself """
from datetime import datetime
import arrow
from arrow import Arrow


def players_sorted_by_key(tracked_players: list, key: str):
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


def get_arrow_date_to_use(day: str) -> Arrow:
    """ Returns the arrow date for the given date string """
    if day:
        date_parts = day.split("-")
        date_to_use = arrow.get(
            datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])),
            'US/Pacific'
        )
    else:
        date_to_use = arrow.now('US/Pacific')
    return date_to_use
