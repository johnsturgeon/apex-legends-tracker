""" This module contains all the controllers for each of the views """
from apex_db_helper import ApexDBHelper, ApexDBGameEvent, filter_game_list
from apex_legends_api.al_domain import DataTracker


class IndexViewController:
    """ Class for performing stats on a set of games """

    def __init__(
            self,
            db_helper: ApexDBHelper,
            start_timestamp,
            end_timestamp):
        query_filter: dict = {
            "eventType": "Game",
            "timestamp": {
                "$gte": start_timestamp,
                "$lte": end_timestamp
            }
        }
        game_list: list = list(
            db_helper.event_collection.find(query_filter)
        )
        if len(game_list) == 0:
            raise Exception("Found no games for player")
        self._game_list: list = []
        for game in game_list:
            game_event: ApexDBGameEvent = ApexDBGameEvent(game)
            self._game_list.append(game_event)
        self.tracked_players: list = []
        player_list = db_helper.get_tracked_players()
        for player in player_list:
            self.tracked_players.append(player)
            # 'uid': int(glob['uid']),
            # 'name': glob['name'],
            # 'platform': glob['platform'],
            # 'is_online': realtime['isOnline']

        for player in self.tracked_players:
            uid = player['uid']
            player['games_played'] = self.num_games_played_for_player(uid)
            player['kill_avg'] = self.category_average_for_player(uid, 'kills')
            player['wins'] = self.category_total_for_player(uid, 'wins')
            player['damage_avg'] = self.category_average_for_player(uid, 'damage')

    def num_games_played_for_player(self, uid: int) -> int:
        """ return the number of games played by a player """
        return len(filter_game_list(self._game_list, uid=uid))

    def category_total_for_player(self, uid: int, category: str) -> int:
        """ returns the category total for each player"""
        total = 0
        filtered_list = filter_game_list(
            self._game_list,
            uid=uid,
            category=category
        )
        game: ApexDBGameEvent
        for game in filtered_list:
            total += game.category_total(category)
        return total

    def category_average_for_player(self, uid: int, category: str) -> float:
        """ Returns the average for the category for a given player """
        average = 0.0
        total = self.category_total_for_player(uid, category)
        num_games = self.num_games_played_for_player(uid)
        if num_games:
            average = total / num_games

        return average

    def max_category(self, category: str) -> int:
        """ Returns the maximum category total for the day """
        max_category: int = 0
        for player in self.tracked_players:
            uid = player['uid']
            max_category = max(max_category, self.category_total_for_player(uid, category))

        return max_category

    def category_total(self, category: str):
        """ Returns the total for a given category"""
        category_total: int = 0
        for player in self.tracked_players:
            category_total += self.category_total_for_player(uid=player['uid'], category=category)
        return category_total

    def max_category_average(self, category: str) -> float:
        """ Return the maximum category average for set of games """
        max_average = 0.0
        for player in self.tracked_players:
            max_average = max(
                max_average,
                self.category_average_for_player(player['uid'], category)
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


class DayByDayViewController():
    """ Class for giving player game stats """

    def __init__(self, db_helper: ApexDBHelper, player_uid: int):
        self.player = db_helper.get_tracked_player_by_uid(player_uid)
        query_filter: dict = {
            "eventType": "Game",
            "uid": str(player_uid)
        }
        game_list: list = list(
            db_helper.event_collection.find(query_filter)
        )
        if len(game_list) == 0:
            raise Exception("Found no games for player ")
        # self._category_totals_by_day: dict = {}
        # self._game_list_by_day: dict = {}
        self._game_list: list = []
        self._days_played: set = set()
        for game in game_list:
            game_event: ApexDBGameEvent = ApexDBGameEvent(game)
            self._game_list.append(game_event)
            self._days_played.add(game_event.day)

    def category_total(self, category: str, day: str = None, legend: str = None) -> int:
        """ returns the category total for each day"""
        total = 0
        for game in filter_game_list(self._game_list, category, day, legend):
            if game.category_total(category) is not None:
                total += game.category_total(category)
        return total

    def category_average(self, category: str, day: str = None, legend: str = None) -> float:
        """ Returns the average for the day """
        total = self.category_total(category, day, legend)
        num_games = len(filter_game_list(self._game_list, category, day, legend))
        if num_games > 0:
            return total / num_games
        return 0.0

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

    def games_played(self, day: str = None, legend: str = None):
        """ Returns a list of games played that day """
        return filter_game_list(self._game_list, day=day, legend=legend)
