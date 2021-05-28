""" This module contains all the controllers for each of the views """
from typing import List

import arrow

from apex_db_helper import ApexDBHelper, ApexDBGameEvent, filter_game_list


class BaseGameViewController:
    """ Base controller for all views that deal with games """
    def __init__(self, db_helper: ApexDBHelper, query_filter: dict):
        # we must convert this to a string for the db (for now)
        if query_filter.get('uid'):
            query_filter['uid'] = str(query_filter['uid'])
        game_list: list = list(
            db_helper.event_collection.find(query_filter)
        )
        self._game_list: List[ApexDBGameEvent] = []
        for game in game_list:
            game_event: ApexDBGameEvent = ApexDBGameEvent(game)
            self._game_list.append(game_event)

    @property
    def game_list(self):
        """ expose protected list """
        return self._game_list

    def games_played(self, uid: int = None, day: str = None, legend: str = None):
        """ Returns a list of games played that day """
        return filter_game_list(self.game_list, uid=uid, day=day, legend=legend)

    def category_total(self, category: str, day: str = None, uid: int = None, legend: str = None):
        """ Returns a filtered category total """
        total = 0
        filtered_list = filter_game_list(
            self.game_list,
            uid=uid,
            day=day,
            category=category,
            legend=legend
        )
        game: ApexDBGameEvent
        for game in filtered_list:
            total += game.category_total(category)
        return total

    def category_average(
            self,
            category: str,
            day: str = None,
            uid: int = None,
            legend: str = None
    ) -> float:
        """ Returns the average for the category for a given player """
        average = 0.0
        total = self.category_total(category, day=day, uid=uid, legend=legend)
        num_games = len(self.games_played(uid=uid, day=day, legend=legend))
        if num_games:
            average = total / num_games

        return average


class IndexViewController(BaseGameViewController):
    """ Class for performing stats on a set of games """

    def __init__(self, db_helper: ApexDBHelper, start_timestamp, end_timestamp):
        query_filter: dict = {
            "eventType": "Game",
            "timestamp": {
                "$gte": start_timestamp,
                "$lte": end_timestamp
            }
        }
        super().__init__(db_helper, query_filter)
        self.tracked_players: list = []
        player_list = db_helper.get_tracked_players()
        for player in player_list:
            self.tracked_players.append(player)

        for player in self.tracked_players:
            uid = player['uid']
            player['games_played'] = len(self.games_played(uid=uid))
            player['kill_avg'] = self.category_average('kills', uid=uid)
            player['wins'] = self.category_total('wins', uid=uid)
            player['damage_avg'] = self.category_average('damage', uid=uid)

    def max_category(self, category: str) -> int:
        """ Returns the maximum category total for the day """
        max_category: int = 0
        for player in self.tracked_players:
            if category == 'games':  # special case for games
                max_category = max(max_category, player['games_played'])
            else:
                uid = player['uid']
                max_category = max(max_category, self.category_total(category, uid=uid))

        return max_category

    def max_category_average(self, category: str) -> float:
        """ Return the maximum category average for set of games """
        max_average = 0.0
        for player in self.tracked_players:
            max_average = max(
                max_average,
                self.category_average(category, uid=player['uid'])
            )
        return max_average

    def players_sorted_by_key(self, key: str):
        """ returns back a list of players sorted by the category """
        # one or the other but not both
        if key == 'name':
            sorted_players = sorted(self.tracked_players, key=lambda item: item[key].casefold())
        else:
            sorted_players = sorted(self.tracked_players, key=lambda item: item[key], reverse=True)
        return sorted_players


class DayByDayViewController(BaseGameViewController):
    """ Class for giving player game stats """

    def __init__(self, db_helper: ApexDBHelper, player_uid: int):
        query_filter: dict = {
            "eventType": "Game",
            "uid": str(player_uid)
        }
        super().__init__(db_helper, query_filter)
        self.player = db_helper.get_tracked_player_by_uid(player_uid)
        self._days_played: set = set()
        for game in self.game_list:
            self._days_played.add(game.day)

    def days_played(self, reverse: bool = True) -> list:
        """ returns a list of days (format 'YYYY-MM-DD') that the player actually PLAYED a game """
        return sorted(self._days_played, reverse=reverse)

    def get_legends_played(self, day: str) -> list:
        """ Returns a list of legends played on a given day """
        legend_set: set = set()
        game: ApexDBGameEvent
        for game in filter_game_list(self._game_list, category=None, day=day):
            legend_set.add(game.legend_played)
        return sorted(legend_set)


class ProfileViewController:
    """ View controller for the player detail page """
    def __init__(self, db_helper: ApexDBHelper, player_uid: int):
        self.player = db_helper.get_tracked_player_by_uid(player_uid)

    def get_platform(self) -> str:
        """ Return friendly version of the player's platform"""
        platform: str = self.player['platform']
        if platform == 'X1':
            return 'Xbox'
        if platform == 'PS4':
            return 'Playstation'
        return platform


class BattlePassViewController:
    """ View controller for the battlepass page """
    def __init__(self, db_helper: ApexDBHelper):
        self.tracked_players: list = []
        player_list = db_helper.get_tracked_players()
        for player in player_list:
            self.tracked_players.append(player)

        self.battlepass_info = db_helper.battlepass_info_collection.find_one({})
        start_date = arrow.get(self.battlepass_info['start_date'])
        end_date = arrow.get(self.battlepass_info['end_date'])
        today = arrow.now('US/Pacific')
        battlepass_max = self.battlepass_info['max_battlepass']
        days_progressed = (today - start_date).days
        days_in_season = (end_date - start_date).days
        self.battlepass_info['days_in_season'] = days_in_season
        self.battlepass_info['days_progressed'] = days_progressed
        level_per_day_rate = battlepass_max / days_in_season
        self.battlepass_info['goal_levels'] = level_per_day_rate * days_progressed

    def players_sorted_by_key(self, key: str):
        """ returns back a list of players sorted by the category """
        # one or the other but not both
        if key == 'name':
            sorted_players = sorted(self.tracked_players, key=lambda item: item[key].casefold())
        else:
            sorted_players = sorted(self.tracked_players, key=lambda item: item[key], reverse=True)
        return sorted_players


