""" Module for providing stats from the ALPlayer object """
from typing import Tuple
import arrow
from apex_legends_api import ALPlayer
from apex_legends_api.al_domain import DataTracker, GameEvent
from apex_legends_api.al_base import ALEventType


class PlayerData:
    """ A wrapper class for a player's stats """
    def __init__(self, player: ALPlayer):
        self.player = player

    def data_for_category_day_average(self, tracker_category: str) -> Tuple[list, list]:
        """ Creates a bar trace for a plotly bar graph """
        damage_day: dict = dict()
        game_day: dict = dict()
        for day in self.days_played():
            for game in self.games_played(day=day):
                if day not in damage_day:
                    damage_day[day] = 0
                    game_day[day] = 0
                tracker: DataTracker
                for tracker in game.game_data_trackers:
                    print(tracker.category)
                    if tracker.category == tracker_category:
                        damage_day[day] += int(tracker.value)
                        game_day[day] += 1

        x_array: list = list()
        y_array: list = list()
        for key in damage_day:
            if damage_day[key] > 0:
                x_array.append(key)
                y_array.append(int((damage_day[key] / game_day[key])))
        return x_array, y_array

    def days_played(self, only_games: bool = True) -> list:
        """ returns a list of days (format 'YYYY-MM-DD') that the player actually PLAYED a game """
        dict_of_days: dict = dict()
        event: GameEvent
        for event in self.player.events:
            is_game: bool = event.event_type == ALEventType.GAME
            if not is_game and only_games:
                continue
            day_key = str(
                arrow.get(event.timestamp).to('local').format('YYYY-MM-DD')
            )
            dict_of_days[day_key] = ""

        return list(dict_of_days.keys())

    def games_played(self, day: str) -> list[GameEvent]:
        """ Return the list of games played for a given day """
        games: list[GameEvent] = list()
        for match in self.player.events:
            if match.event_type == ALEventType.GAME:
                match.__class__ = GameEvent
                day_key = str(
                    arrow.get(match.timestamp).to('local').format('YYYY-MM-DD')
                )
                if day_key == day:
                    games.append(match)
        return games

    def category_total(self, day: str, category: str) -> int:
        """ Return the total for a given category on a given day """
        total = 0
        game: GameEvent
        for game in self.games_played(day):
            tracker: DataTracker
            for tracker in game.game_data_trackers:
                if tracker.category == category:
                    total += tracker.value
                elif 'season' in tracker.category:
                    print(tracker.category)
        return total

    def category_day_average(self, day: str, category: str) -> float:
        """ Return the average for a given category on a given day """
        avg: float = 0.0
        games_played = len(self.games_played(day))
        if games_played:
            avg = self.category_total(day, category) / len(self.games_played(day))
        return avg

    def category_rolling_average(self, day: str, category: str, rolling_days: int) -> float:
        """
        Calculates a rolling average for a category

        Notes:
            The rolling average will be for a given category starting at the given day, and looking
            back over the number of rolling_days
        """
        start_date = arrow.get(day)
        rolling_total: float = 0.0
        rolling_day_count: int = rolling_days
        for day_played in self.days_played():
            arrow_day = arrow.get(day_played)
            if arrow_day <= start_date and rolling_day_count > 0:
                rolling_day_count -= 1
                rolling_total += self.category_day_average(day, category)

        return rolling_total / rolling_days