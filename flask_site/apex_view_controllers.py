""" This module contains all the controllers for each of the views """
from apex_db_helper import ApexDBHelper, ApexDBGameEvent
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
        self._game_list_by_uid: dict = {}
        self._category_totals_by_uid: dict = {}
        self._category_totals_by_day: dict = {}
        self.tracked_players: list = []
        player_list = db_helper.get_tracked_players()
        for player in player_list:
            self.tracked_players.append(player)
            # 'uid': int(glob['uid']),
            # 'name': glob['name'],
            # 'platform': glob['platform'],
            # 'is_online': realtime['isOnline']

        for game in game_list:
            game_event: ApexDBGameEvent = ApexDBGameEvent(game)
            uid: int = int(game_event.uid)
            if uid not in self._game_list_by_uid:
                self._game_list_by_uid[uid]: list = []
            self._game_list_by_uid[uid].append(game_event)
            if uid not in self._category_totals_by_uid:
                self._category_totals_by_uid[uid]: dict = {}
            tracker: DataTracker
            for tracker in game_event.game_data_trackers:
                if tracker.category not in self._category_totals_by_uid[uid]:
                    self._category_totals_by_uid[uid][tracker.category] = 0
                self._category_totals_by_uid[uid][tracker.category] += tracker.value
        # games are a special category, so let's just make it up here
        for uid in self._game_list_by_uid:
            self._category_totals_by_uid[uid]['games'] = len(self._game_list_by_uid[uid])

        for player in self.tracked_players:
            uid = player['uid']
            player['games_played'] = self.num_games_played_for_player(uid)
            player['kill_avg'] = self.category_average_for_player(uid, 'kills')
            player['wins'] = self.category_total_for_player(uid, 'wins')
            player['damage_avg'] = self.category_average_for_player(uid, 'damage')

    def num_games_played_for_player(self, uid: int) -> int:
        """ re"""
        games = self._game_list_by_uid.get(uid)
        if games:
            return len(games)
        return 0

    def category_total_for_player(self, uid: int, category: str) -> int:
        """ returns the category total for each player"""
        total = 0
        player = self._category_totals_by_uid.get(uid)
        if player:
            category_total = self._category_totals_by_uid[uid].get(category)
            if category_total:
                total = self._category_totals_by_uid[uid][category]
        return total

    def category_average_for_player(self, uid: int, category: str) -> float:
        """ Returns the average for the category for a given player """
        average = 0.0
        total = self.category_total_for_player(uid, category)
        if total and self._game_list_by_uid.get(uid):
            average = total / len(self._game_list_by_uid.get(uid))

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
        self.player = db_helper.get_player_by_uid(player_uid)
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
        for game in game_list:
            game_event: ApexDBGameEvent = ApexDBGameEvent(game)
            self._game_list.append(game_event)

        #     day = game_event.day
        #     if not self._game_list_by_day.get(day):
        #         self._game_list_by_day[day] = []
        #     self._game_list_by_day[day].append(game_event)
        #
        #     if not self._category_totals_by_day.get(day):
        #         self._category_totals_by_day[day] = {}
        #     tracker: DataTracker
        #     for tracker in game_event.game_data_trackers:
        #         if not self._category_totals_by_day[day].get(tracker.category):
        #             self._category_totals_by_day[day][tracker.category] = 0
        #         self._category_totals_by_day[day][tracker.category] += tracker.value
        # # games are a special category, so let's just make it up here
        # for day in self._game_list_by_day:
        #     self._category_totals_by_day[day]['games'] = len(self._game_list_by_day[day])

    def category_total(self, category: str, day: str = None, legend: str = None) -> int:
        """ returns the category total for each day"""
        total = 0
        for game in self.filter_game_list(category, day, legend):
            game_total = game.categories.get(category)
            if game_total:
                total += game_total
        return total

    def category_average(self, category: str, day: str = None, legend: str = None) -> float:
        """ Returns the average for the day """
        total = self.category_total(category, day, legend)
        num_games = self.filter_game_list(category, day, legend)
        if num_games > 0:
            return total / num_games

    def days_played(self) -> list:
        """ returns a list of days (format 'YYYY-MM-DD') that the player actually PLAYED a game """
        return sorted(self._category_totals_by_day.keys(), reverse=True)

    def filter_game_list(self,
                         category: str = None,
                         day: str = None,
                         legend: str = None
                         ) -> list:
        """ Returns a list of the games played on a specific day """
        filtered_list: list = []
        for game in self._game_list:
            add_list: bool = True
            if day and game.day != day:
                add_list = False
            if legend and game.legend_played != legend:
                add_list = False
            if category and game.categories.get(category) != category:
                add_list = False
            if add_list:
                filtered_list.append(game)
        return filtered_list

    def get_legends_played(self, day: str) -> list:
        """ Returns a list of legends played on a given day """
        legend_set: set = set()
        game: ApexDBGameEvent
        for game in self.games_played(day):
            legend_set.add(game.legend_played)
        return list(legend_set)
