""" This module contains all the controllers for each of the views """
from typing import List, Tuple, Optional
import json
from dataclasses import dataclass

import arrow
import pymongo
from arrow import Arrow

from apex_db_helper import ApexDBHelper, filter_game_list
from models.config import Config
from models import GameEvent, RankTier, Division, RankedDivisionInfo, Player, Season
from apex_utilities import players_sorted_by_key
import plotly.graph_objects as go
import plotly.utils as ut


@dataclass
class RankedGameDay:
    """ Container for ranked info"""
    end_of_day_score: int
    number_of_games: int


class BaseGameViewController:
    """ Base controller for all views that deal with games """

    def __init__(self,
                 db_helper: ApexDBHelper,
                 query_filter: dict,
                 game_mode: Optional[str] = None):
        # we must convert this to a string for the db (for now)
        if query_filter.get('uid'):
            query_filter['uid'] = str(query_filter['uid'])

        game_list: List[GameEvent] = db_helper.event_collection.get_games(
            additional_filter=query_filter
        )
        self._game_list: List[GameEvent] = list()
        for game in game_list:
            if game_mode and game_mode != game.game_mode:
                continue
            self._game_list.append(game)

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
        game: GameEvent
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

    def __init__(self,
                 db_helper: ApexDBHelper,
                 start_timestamp: int,
                 end_timestamp: int,
                 game_mode: str = None):
        query_filter: dict = {
            "eventType": "Game",
            "timestamp": {
                "$gte": start_timestamp,
                "$lte": end_timestamp
            }
        }
        super().__init__(db_helper, query_filter, game_mode)
        self.tracked_players = db_helper.player_collection.get_tracked_players()

        for player in self.tracked_players:
            uid = player.uid
            player.games_played = len(self.games_played(uid=uid))
            player.kills_avg = self.category_average('kills', uid=uid)
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

    def __init__(self, db_helper: ApexDBHelper, player: Player):
        self.player = player
        query_filter: dict = {
            "eventType": "Game",
            "uid": str(player.uid)
        }
        super().__init__(db_helper, query_filter)
        self._days_played: set = set()
        for game in self.game_list:
            self._days_played.add(game.day_of_event)

    def days_played(self, reverse: bool = True) -> list:
        """ returns a list of days (format 'YYYY-MM-DD') that the player actually PLAYED a game """
        return sorted(self._days_played, reverse=reverse)

    def get_legends_played(self, day: str) -> list:
        """ Returns a list of legends played on a given day """
        legend_set: set = set()
        game: GameEvent
        for game in filter_game_list(self._game_list, category=None, day=day):
            legend_set.add(game.legend_played)
        return sorted(legend_set)


class LeaderboardViewController(IndexViewController):
    """ Class for showing the leaderboard for kills, wins, damage """
    def __init__(self, db_helper: ApexDBHelper, start_timestamp: int, end_timestamp: int, clan):
        super().__init__(db_helper, start_timestamp, end_timestamp, game_mode="BR")
        self.leader_player_list: List[Player] = list()
        category_list = ['damage_total', 'kills_total', 'xp_total', 'wins']
        for player in self.tracked_players:
            if not player.games_played or (clan and player.clan != clan):
                continue
            player.damage_total = self.category_total('damage', uid=player.uid)
            player.kills_total = self.category_total('kills', uid=player.uid)
            player.xp_total = self.category_total('xp_progress', uid=player.uid)
            player.minute_total = self.category_total('game_length', uid=player.uid)
            self.leader_player_list.append(player)

        for player in self.leader_player_list:
            player.point_total = 0
            for category in category_list:
                player.point_total += self.points_for_category(category, player.uid)

    def points_for_category(self, category: str, player_uid: int) -> int:
        """ Returns the points for a given category """
        sorted_players: List[Player] = self.players_sorted_by_key(category)
        max_points: int = len(sorted_players)
        position_index: int = 0
        current_player: Optional[Player] = None
        for player in sorted_players:
            if player.uid == player_uid:
                current_player = player
                break
            position_index += 1
        searching_for_players: bool = True
        my_total = getattr(current_player, category)
        if my_total == 0:
            return 0
        while position_index and searching_for_players:
            player_above = sorted_players[position_index-1]
            player_above_total = getattr(player_above, category)
            if my_total == player_above_total:
                position_index -= 1
            else:
                searching_for_players = False
        return max_points - position_index

    def players_sorted_by_key(self, key: str) -> List[Player]:
        """ Wrapper for utility function """
        return players_sorted_by_key(self.leader_player_list, key)


class DayDetailViewController:
    """ View Controller for the Day Detail """

    def __init__(self, db_helper: ApexDBHelper, player: Player, day: Arrow):
        self.player = player
        starting_timestamp = day.floor('day').int_timestamp
        ending_timestamp = day.shift(days=+1).floor('day').int_timestamp
        self.leaderboard_view_controller: LeaderboardViewController = LeaderboardViewController(
            db_helper=db_helper,
            start_timestamp=starting_timestamp,
            end_timestamp=ending_timestamp,
            clan=None
        )
        start_day = day.format('YYYY-MM-DD')
        end_day = day.shift(days=+1).format('YYYY-MM-DD')
        self.all_games: List[GameEvent] = db_helper.event_collection.get_games(
            start_end_day=(start_day, end_day), sort=pymongo.DESCENDING
        )
        self.games: List[GameEvent] = filter_game_list(self.all_games, uid=player.uid)
        self.player.minute_total = self.category_total('game_length')

    def category_total(self, category: str) -> int:
        """ Returns the category total """
        total = 0
        for game in self.games:
            total += int(game.category_total(category))
        return total

    def category_average(self, category: str) -> float:
        """ Returns the category average """
        total_games = len(self.games)
        if total_games:
            return self.category_total(category) / total_games
        return 0

    def avg_time_played(self):
        """ Returns the average time played in minutes / seconds """
        return_string: str = ""
        total_time = self.player.minute_total
        if len(self.games) > 0:
            avg_minutes: float = total_time / len(self.games)
            avg_seconds = avg_minutes * 60
            minutes, seconds = divmod(avg_seconds, 60)
            round_minutes = round(minutes)
            round_seconds = round(seconds)
            if round_minutes:
                return_string += f"{round_minutes}m"
            if round_seconds:
                return_string += f" {round_seconds}s"
        return return_string

    def category_max(self, category: str) -> int:
        """ Returns the max for the category"""
        max_category: int = 0
        for game in self.games:
            max_category = max(game.category_total(category), max_category)
        return max_category

    def category_squad_total(self, in_game: GameEvent, category: str) -> int:
        """ Returns the total of the squad for a game """
        total: int = in_game.category_total(category)
        for game in self.find_games_near_mine(in_game):
            total += game.category_total(category)
        return total

    def find_games_near_mine(self, in_game: GameEvent) -> List[GameEvent]:
        """Find games that might be people I played with """
        games_found: List[GameEvent] = list()
        gt_padding = 10
        gl_padding = 1
        gt_range = range(in_game.timestamp-gt_padding, in_game.timestamp+gt_padding+1)
        gl_range = range(in_game.game_length-gl_padding, in_game.game_length+gl_padding+1)
        for game in self.all_games:
            if game.uid != in_game.uid:
                if game.is_ranked_game == in_game.is_ranked_game and \
                        game.timestamp in gt_range and game.game_length in gl_range:
                    games_found.append(game)
        return games_found

    def total_time_played(self) -> str:
        """ Returns a formatted string for the total time played """
        total_time = self.player.minute_total
        hours, minutes = divmod(total_time, 60)
        return f"{hours}h {minutes}m"

    def leaderboard_points(self, key: str = 'point_total') -> int:
        """ Returns the player's point total for the day """
        for player in self.leaderboard_view_controller.players_sorted_by_key(key):
            if player.name == self.player.name:
                return player.point_total
        return 0

    def leaderboard_place(self) -> str:
        """
        Convert an integer into its ordinal representation::
            make_ordinal(0)   => '0th'
            make_ordinal(3)   => '3rd'
            make_ordinal(122) => '122nd'
            make_ordinal(213) => '213th'
        """
        num = self.leaderboard_position()
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(num % 10, 4)]
        if 11 <= (num % 100) <= 13:
            suffix = 'th'
        return str(num) + suffix

    def leaderboard_position(self, key: str = 'point_total') -> int:
        """ Returns the string of the placement on the leaderboard """

        index: int = 0
        place: int = 0
        previous_key_total: int = -1
        for player in self.leaderboard_view_controller.players_sorted_by_key(key):
            index += 1
            key_total: int = int(getattr(player, key))
            if key_total != previous_key_total:
                place = index
            if player.name == self.player.name:
                break
            previous_key_total = key_total

        return place

    def leaderboard_player_count(self) -> int:
        """ Returns the number of players on the leaderboard """
        return len(self.leaderboard_view_controller.leader_player_list)


class ProfileViewController:
    """ View controller for the player detail page """
    def __init__(self, db_helper: ApexDBHelper, player: Player):
        self.player = player
        self._config = db_helper.config
        self.season: Season = db_helper.season_collection.get_current_season()
        self._ranked_games = db_helper.event_collection.get_ranked_games(
            season=self.season,
            player_uid=self.player.uid
        )

    def get_platform_logo(self) -> str:
        """ Return friendly version of the player's platform"""
        platform: str = self.player.platform
        if platform == 'X1':
            return 'xbox.svg'
        if platform == 'PS4':
            return 'playstation.svg'
        # default
        return 'origin.svg'

    def get_ranked_plot_data(self) -> Tuple[list, list, list]:
        """ Return ranked event lists """
        rank_dict: dict = self.create_ranked_dict()
        x_array: list = list()
        y_array: list = list()
        text_array: list = list()
        rank_info: RankedGameDay
        prev_rank: int = 0
        distance_to_next: int = 0
        for day, rank_info in rank_dict.items():
            rank_tier: RankTier = self._config.get_rank_div_tier_for_points(
                rank_info.end_of_day_score
            )
            distance_token: str = '🟢'
            distance_from_prev: int = rank_info.end_of_day_score - prev_rank
            if distance_from_prev < 0:
                distance_token = '🔴'
            prev_rank = rank_info.end_of_day_score
            x_array.append(day)
            y_array.append(rank_info.end_of_day_score)
            distance_to_next = rank_tier.distance_to_next
            text_array.append(
                f"{rank_tier.division} {rank_tier.tier}<br />"
                f"Ranked Games Played: {rank_info.number_of_games}<br />"
                f"RP change from previous {distance_token}: {distance_from_prev}"
            )
        if text_array:
            text_array[-1] += f"<br />RP to next tier {distance_to_next}"

        return x_array, y_array, text_array

    def create_ranked_dict(self) -> dict:
        """ Create the ranked dictionary """
        rank_dict: dict = {}
        game_count: int = 0
        ranked_game: GameEvent
        for ranked_game in self._ranked_games:
            date: str = ranked_game.day_of_event
            score: int = int(ranked_game.current_rank_score)
            if not rank_dict.get(date):
                game_count = 0
            game_count += 1
            rank_dict[date] = RankedGameDay(score, game_count)
        return rank_dict

    def add_rank_bands_to_fig(self, fig):
        """ adds a rank band to the figure """
        y_pos = 0
        div_info: RankedDivisionInfo = self._config.ranked_division_info
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
        # add vertical line for split
        if self.season.ranked_split_date:
            _, end_date = self.season.first_ranked_split_dates
            fig.add_vline(
                x=end_date,
                row="hi",
                col="col",
                line_dash="dash",
                line_width=1,
                line_color="#F5DEB3"
            )
            fig.add_annotation(
                x=end_date,
                text="New Split",
                yanchor="top",
                font_color="#F5DEB3",
                borderpad=3,
                bordercolor="#F5DEB3",
                bgcolor="#412020",
                align="center",
                valign="top",
                showarrow=False,
                yref="paper",
                y=1.1
            )

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
        for division in self._config.ranked_division_info.divisions:
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
        self.tracked_players: List[Player] = db_helper.player_collection.get_tracked_players()
        self.config: Config = db_helper.config
        self.season: Season = db_helper.season_collection.get_current_season()
        self.battlepass_data: dict = dict()
        start_date = arrow.get(self.season.start_date)
        end_date = arrow.get(self.season.end_date)
        today = arrow.now('US/Pacific')
        battlepass_max = self.config.battlepass_goal
        days_progressed = (today - start_date).days
        days_in_season = (end_date - start_date).days
        self.battlepass_data['battlepass_goal'] = self.config.battlepass_goal
        self.battlepass_data['days_in_season'] = days_in_season
        self.battlepass_data['days_progressed'] = days_progressed
        level_per_day_rate = battlepass_max / days_in_season
        # clamp goal level so we don't divide by zero
        goal_level: float = max(1.0, float(level_per_day_rate * days_progressed))
        self.battlepass_data['goal_levels'] = goal_level

    def players_sorted_by_key(self, key: str) -> List[Player]:
        """ Wrapper for utility function"""
        return players_sorted_by_key(self.tracked_players, key)


class ClaimProfileViewController:
    """ View controller for the 'claim profile' page """
    def __init__(self, db_helper: ApexDBHelper):
        self.player_collection = db_helper.player_collection
        player: Player
        self.tracked_players: List[Player] = list()
        for player in self.player_collection.get_tracked_players():
            if not player.discord_id:
                self.tracked_players.append(player)
        self.tracked_players = players_sorted_by_key(self.tracked_players, 'name')

    def claim_profile_with_discord_id(self, player_uid: int, discord_id: int):
        """ Save a player with the discord ID """
        player: Player
        for player in self.tracked_players:
            if player_uid == player.uid:
                player.discord_id = discord_id
                self.player_collection.save_player(player)
                break
