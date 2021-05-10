""" Module for providing stats from the ALPlayer object """
from typing import Tuple
import arrow
from apex_legends_api import ALPlayer
from apex_legends_api.al_domain import DataTracker, GameEvent, Legend
from apex_legends_api.al_base import ALEventType


class PlayerData:
    """ A wrapper class for a player's stats """
    def __init__(self, player: ALPlayer):
        self.player = player
        self._games_played: dict = {}
        self._days_played_only_games: dict = {}
        self._days_played: dict = {}

    def data_for_category_day_average(
            self,
            tracker_category: str,
            legend: str = ""
    ) -> Tuple[list, list]:
        """ Creates a bar trace for a plotly bar graph """
        damage_day: dict = dict()
        game_day: dict = dict()
        for day in self.days_played():
            for game in self.games_played(day=day, legend=legend):
                if day not in damage_day:
                    damage_day[day] = 0
                    game_day[day] = 0
                tracker: DataTracker
                for tracker in game.game_data_trackers:
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
        if only_games:
            dict_of_days = self._days_played_only_games
        else:
            dict_of_days = self._days_played

        if dict_of_days:
            return dict_of_days

        event: GameEvent
        for event in self.player.events:
            is_game: bool = event.event_type == ALEventType.GAME
            if not is_game and only_games:
                continue
            day_key = str(
                arrow.get(event.timestamp).to('US/Pacific').format('YYYY-MM-DD')
            )
            dict_of_days[day_key] = ""
        if only_games:
            self._days_played_only_games = dict_of_days
        else:
            self._days_played = dict_of_days
        return list(sorted(dict_of_days.keys(), reverse=True))

    def games_played(self, day: str, legend: str = "") -> list[GameEvent]:
        """ Return the list of games played for a given day """
        unfiltered_games: list[GameEvent] = list()
        filtered_games: list[GameEvent] = list()
        if day in self._games_played:
            unfiltered_games = self._games_played[day]
        else:
            for match in self.player.events:
                if match.event_type == ALEventType.GAME:
                    match.__class__ = GameEvent
                    day_key = str(
                        arrow.get(match.timestamp).to('local').format('YYYY-MM-DD')
                    )
                    if day_key == day:
                        unfiltered_games.append(match)
            self._games_played[day] = unfiltered_games

        if legend:
            for game in unfiltered_games:
                if game.legend_played == legend:
                    filtered_games.append(game)
        else:
            filtered_games = unfiltered_games
        return filtered_games

    def category_total(self, day: str, category: str, legend: str = "") -> int:
        """ Return the total for a given category on a given day """
        total = 0
        if category == 'games':
            return len(self.games_played(day))

        game: GameEvent
        for game in self.games_played(day, legend):
            tracker: DataTracker
            for tracker in game.game_data_trackers:
                if tracker.category == category:
                    total += tracker.value
                elif 'season' in tracker.category:
                    ...
        return total

    def category_day_average(self, day: str, category: str, legend: str = "") -> float:
        """ Return the average for a given category on a given day """
        avg: float = 0.0
        games_played = len(self.games_played(day, legend))
        if games_played:
            avg = self.category_total(day, category, legend) / len(self.games_played(day, legend))
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

    def get_legends_played(self, day: str) -> list:
        """ Returns a list of legends played for a given day """
        legends: dict = {}
        game: GameEvent
        for game in self.games_played(day):
            if not game.legend_played:
                continue

            legends[game.legend_played] = ""

        return list(legends.keys())

    def is_online(self) -> bool:
        """ Returns True if the player is online"""
        return self.player.realtime_info.is_online

    def lifetime_total_for_trackers(self) -> list:
        """
        Returns the lifetime total for each tracker in a dict
        """
        tracker_totals: dict = {}
        legend: Legend
        for legend in self.player.all_legends:
            tracker: DataTracker
            for tracker in legend.data_trackers:
                if tracker.key not in tracker_totals:
                    tracker_totals[tracker.key] = {
                        'tracker_name': tracker.name,
                        'tracker_key': tracker.key,
                        'tracker_category': tracker.category,
                        'lifetime_total': tracker.value,
                        'legends': [legend.name]
                    }
                else:
                    tracker_totals[tracker.key]['lifetime_total'] += tracker.value
                    if legend.name not in tracker_totals[tracker.key]['legends']:
                        tracker_totals[tracker.key]['legends'].append(legend.name)

        return list(tracker_totals.values())

    def lifetime_total_for_categories(self) -> list:
        """
        Returns the lifetime total for each tracker in a dict
        """
        category_totals: dict = {}
        for tracker in self.lifetime_total_for_trackers():
            category_key = tracker['tracker_category']
            if category_key not in category_totals:
                category_totals[category_key] = {
                    'category_name': category_key.capitalize(),
                    'category_key': category_key,
                    'category_lifetime_total': tracker['lifetime_total']
                }
            else:
                category_totals[
                    category_key
                ]['category_lifetime_total'] += tracker['lifetime_total']

        return list(category_totals.values())
