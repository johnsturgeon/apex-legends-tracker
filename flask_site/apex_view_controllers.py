""" This module contains all the controllers for each of the views """
from typing import List, Tuple
import json
from dataclasses import dataclass
import arrow
from apex_db_helper import ApexDBHelper, ApexDBGameEvent, filter_game_list
from models import RankedGameEvent, RankTier, Division, RankedDivisionInfo
from apex_utilities import players_sorted_by_key
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
        self.tracked_players = db_helper.get_tracked_players()

        for player in self.tracked_players:
            uid = player.uid
            player.games_played = len(self.games_played(uid=uid))
            player.kill_avg = self.category_average('kills', uid=uid)
            player.wins = self.category_total('wins', uid=uid)
            player.damage_avg = self.category_average('damage', uid=uid)

    def max_category(self, category: str) -> int:
        """ Returns the maximum category total for the day """
        max_category: int = 0
        for player in self.tracked_players:
            if category == 'games':  # special case for games
                max_category = max(max_category, player.games_played)
            else:
                uid = player.uid
                max_category = max(max_category, self.category_total(category, uid=uid))

        return max_category

    def max_category_average(self, category: str) -> float:
        """ Return the maximum category average for set of games """
        max_average = 0.0
        for player in self.tracked_players:
            max_average = max(
                max_average,
                self.category_average(category, uid=player.uid)
            )
        return max_average

    def players_sorted_by_key(self, key: str):
        """ Wrapper for utility function"""
        return players_sorted_by_key(self.tracked_players, key)


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
        self._ranked_games = db_helper.get_ranked_games(player_uid)
        self._basic_info = db_helper.basic_info
        self.player = db_helper.get_tracked_player_by_uid(player_uid)

    def get_platform_logo(self) -> str:
        """ Return friendly version of the player's platform"""
        platform: str = self.player['platform']
        if platform == 'X1':
            return 'xbox.svg'
        if platform == 'PS4':
            return 'playstation.svg'
        # default
        return 'origin.svg'

    def get_ranked_plot_data(self) -> Tuple[list, list, list]:
        """ Return ranked event lists """
        @dataclass
        class RankedGameDay:
            """ Container for ranked info"""
            end_of_day_score: int
            number_of_games: int

        rank_dict: dict = {}
        game_count: int = 0
        ranked_game: RankedGameEvent
        for ranked_game in self._ranked_games:
            rank_tier: RankTier
            date: str = ranked_game.day_of_event
            score: int = int(ranked_game.current_rank_score)
            if not rank_dict.get(date):
                game_count = 0
            game_count += 1
            rank_dict[date] = RankedGameDay(score, game_count)
        x_array: list = list()
        y_array: list = list()
        text_array: list = list()
        rank_info: RankedGameDay
        for day, rank_info in rank_dict.items():
            rank_tier: RankTier = self._basic_info.get_rank_div_tier(
                rank_info.end_of_day_score
            )
            x_array.append(day)
            y_array.append(rank_info.end_of_day_score)
            text_array.append(
                f"{rank_tier.division} {rank_tier.tier}<br />"
                f"Ranked Games Played: {rank_info.number_of_games}"
            )
        return x_array, y_array, text_array

    def add_rank_bands_to_fig(self, fig):
        """ adds a rank band to the figure """
        y_pos = 0
        div_info: RankedDivisionInfo = self._basic_info.ranked_division_info
        division: Division
        for division in div_info.divisions:
            opacity = 0.05
            step_increment = division.rp_between_tiers
            step_bg_color = division.color
            for tier in div_info.tiers:
                annotation_text = tier
                fig.add_hrect(y0=y_pos,
                              y1=y_pos + step_increment - 1,
                              line_width=0,
                              fillcolor=step_bg_color,
                              opacity=opacity,
                              annotation_text=annotation_text,
                              annotation_font_size=9
                              )
                y_pos += step_increment
                opacity += 0.06

    def ranked_plot(self):
        """ Create a spline smoothed chart """
        x_axis, y_axis, text_list = self.get_ranked_plot_data()
        fig = go.Figure()
        self.add_rank_bands_to_fig(fig)
        fig.add_trace(go.Scatter(x=x_axis, y=y_axis, name="spline",
                                 text=text_list))
        fig.update_traces(hovertemplate=None)
        fig.update_layout(hovermode="x unified")
        fig.update_layout(hoverlabel=dict(font_color='black', bgcolor='wheat'))
        # initialize with bottom value
        y_tick_value: int = 0
        tick_values: list = [y_tick_value]
        tick_text: list = ['']
        division: Division
        for division in self._basic_info.ranked_division_info.divisions:
            y_tick_value = y_tick_value + (division.rp_between_tiers * 4)
            tick_values.append(y_tick_value - 1)
            tick_text.append(division.name)
        max_y = 10000
        min_y = 0
        if y_axis:
            max_y = max(y_axis)
            min_y = min(y_axis)
            new_min_y: int = min_y
            new_max_y: int = max_y
            for value in tick_values:
                if value < min_y:
                    new_min_y = value
            for value in reversed(tick_values):
                if value > max_y:
                    new_max_y = value
            max_y = new_max_y
            min_y = new_min_y

        fig.update_layout(
            template="plotly_dark",
            legend=dict(y=0.5, traceorder='reversed', font_size=16),
            yaxis_range=[min_y, max_y],
            yaxis=dict(tickvals=tick_values, ticktext=tick_text, tickmode='array')
        )
        return json.dumps(fig, cls=ut.PlotlyJSONEncoder)


class BattlePassViewController:
    """ View controller for the battlepass page """

    def __init__(self, db_helper: ApexDBHelper):
        self.tracked_players: list = []
        player_list = db_helper.get_tracked_players()
        for player in player_list:
            self.tracked_players.append(player)

        self.battlepass_info = db_helper.basic_info.get_season().battlepass_info
        self.battlepass_data: dict = dict()
        start_date = arrow.get(self.battlepass_info.start_date)
        end_date = arrow.get(self.battlepass_info.end_date)
        today = arrow.now('US/Pacific')
        battlepass_max = self.battlepass_info.goal_battlepass
        days_progressed = (today - start_date).days
        days_in_season = (end_date - start_date).days
        self.battlepass_data['days_in_season'] = days_in_season
        self.battlepass_data['days_progressed'] = days_progressed
        level_per_day_rate = battlepass_max / days_in_season
        self.battlepass_data['goal_levels'] = level_per_day_rate * days_progressed

    def players_sorted_by_key(self, key: str):
        """ Wrapper for utility function"""
        return players_sorted_by_key(self.tracked_players, key)
