""" A collection of utilities so I don't repeat myself """
from datetime import datetime
from typing import Tuple

import arrow
from arrow import Arrow


def players_sorted_by_key(tracked_players: list, key: str):
    """ returns back a list of players sorted by the category """
    def my_get_attr(item, key):
        if hasattr(item, key):
            return getattr(item, key)
        return 0

    if key == 'name':
        sorted_players = sorted(
            tracked_players,
            key=lambda item: getattr(item, key).casefold()
        )
    else:
        sorted_players = sorted(
            tracked_players,
            key=lambda item: my_get_attr(item, key), reverse=True
        )
    return sorted_players


def get_arrow_date_prev_next_date_to_use(day: str) -> Tuple[Arrow, str, str, str]:
    """ Returns arrow date, prev and next day strings
    Args:
        day: day to use for calculations
    Returns:
        Tuple[arrow_date_to_use, prev_day, next_day, current_day]
    """
    date_to_use = get_arrow_date_to_use(day)

    if not day:
        day = date_to_use.format('YYYY-MM-DD')
    prev_day = date_to_use.shift(days=-1).format('YYYY-MM-DD')
    today = arrow.now('US/Pacific')
    next_day = None
    if date_to_use < today.shift(days=-1):
        next_day = date_to_use.shift(days=+1).format('YYYY-MM-DD')
    return date_to_use, prev_day, next_day, day


def get_arrow_date_to_use(day: str) -> Arrow:
    """ Returns arrow date to use """
    if day:
        date_parts = day.split("-")
        date_to_use = arrow.get(
            datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])),
            'US/Pacific'
        )
    else:
        date_to_use = arrow.now('US/Pacific')
    return date_to_use
