""" This module contains all the controllers for each of the views """
from typing import List, Tuple
import json
import arrow
from apex_db_helper import ApexDBHelper, ApexDBGameEvent, filter_game_list
import plotly.graph_objects as go
import plotly.utils as ut


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
        self.ranked_events = db_helper.event_collection.find(
            {
                'uid': str(player_uid),
                'eventType': "rankScoreChange"
            }
        )

    def get_platform_logo(self) -> str:
        """ Return friendly version of the player's platform"""
        platform: str = self.player['platform']
        if platform == 'X1':
            return 'xbox.svg'
        if platform == 'PS4':
            return 'playstation.svg'
        # default
        return 'origin.svg'

    def get_ranked_events(self) -> Tuple[list, list]:
        """ Return ranked event lists """
        x_array: list = list()
        y_array: list = list()
        y2_array: list = list()
        skip_one = True
        prev_date = ""
        for ranked_event in self.ranked_events:
            if ranked_event['event']['rankedSeason'] == 'season09_split_1':
                if skip_one:
                    skip_one = False
                    continue
                date = arrow.get(ranked_event['timestamp']).to('US/Pacific').format('YYYY-MM-DD')
                if date != prev_date:
                    prev_date = date
                    x_array.append(date.format())
                    y_array.append(ranked_event['event']['rankScore'])
        return x_array, y_array

    @staticmethod
    def add_rect_to_fig(fig, y_pos, fillcolor, opacity, annotation_text):
        """ adds a rank band to the figure """
        fig.add_hrect(y0=y_pos,
                      y1=y_pos + 300,
                      line_width=0,
                      fillcolor=fillcolor,
                      opacity=opacity,
                      annotation_text=annotation_text,
                      annotation_font_size=9
                      )

    def ranked_plot(self):
        """ Create a spline smoothed chart """
        x_axis, y_axis = self.get_ranked_events()
        max_y = 6000
        min_y = 0
        if y_axis:
            max_y = max(y_axis)
            min_y = min(y_axis)
            count, _ = divmod(max_y, 1200)
            max_y = (count * 1200) + 1200
            count, _ = divmod(min_y, 1200)
            min_y = max((count * 1200), 0)
        fig = go.Figure()
        ProfileViewController.add_rect_to_fig(fig, 0, "#937B44", 0.05, "IV")
        ProfileViewController.add_rect_to_fig(fig, 300, "#937B44", 0.1, "III")
        ProfileViewController.add_rect_to_fig(fig, 600, "#937B44", 0.2, "II")
        ProfileViewController.add_rect_to_fig(fig, 900, "#937B44", 0.3, "Bronze I")
        ProfileViewController.add_rect_to_fig(fig, 1200, "#ddd", 0.05, "IV")
        ProfileViewController.add_rect_to_fig(fig, 1500, "#ddd", 0.1, "III")
        ProfileViewController.add_rect_to_fig(fig, 1800, "#ddd", 0.2, "II")
        ProfileViewController.add_rect_to_fig(fig, 2100, "#ddd", 0.3, "Silver I")
        ProfileViewController.add_rect_to_fig(fig, 2400, "#A2A200", 0.05, "IV")
        ProfileViewController.add_rect_to_fig(fig, 2700, "#A2A200", 0.1, "III")
        ProfileViewController.add_rect_to_fig(fig, 3000, "#A2A200", 0.2, "II")
        ProfileViewController.add_rect_to_fig(fig, 3300, "#A2A200", 0.3, "Gold I")
        ProfileViewController.add_rect_to_fig(fig, 3600, "#ACDFE5", 0.05, "IV")
        ProfileViewController.add_rect_to_fig(fig, 3900, "#ACDFE5", 0.1, "III")
        ProfileViewController.add_rect_to_fig(fig, 4200, "#ACDFE5", 0.2, "II")
        ProfileViewController.add_rect_to_fig(fig, 4500, "#ACDFE5", 0.3, "Platinum I")
        ProfileViewController.add_rect_to_fig(fig, 4800, "#01DAE5", 0.05, "IV")
        ProfileViewController.add_rect_to_fig(fig, 5100, "#01DAE5", 0.1, "III")
        ProfileViewController.add_rect_to_fig(fig, 5400, "#01DAE5", 0.2, "II")
        ProfileViewController.add_rect_to_fig(fig, 5700, "#01DAE5", 0.3, "Diamond I")
        fig.add_trace(go.Scatter(x=x_axis, y=y_axis, name="spline",
                                 text=["tweak line smoothness<br>with 'smoothing' in line object"],
                                 hoverinfo='text+name', mode='lines+markers'))
        fig.update_traces(hoverinfo='text+name')
        fig.update_yaxes(tick0=1200, dtick=1200)
        fig.update_layout(
            template="plotly_dark",
            legend=dict(y=0.5, traceorder='reversed', font_size=16),
            yaxis_range=[min_y, max_y]
        )
        return json.dumps(fig, cls=ut.PlotlyJSONEncoder)


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
