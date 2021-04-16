""" Flask application for Apex Legends API Tracker """
import plotly.graph_objects as go
import plotly.utils as ut
import json
import numpy as np
from flask import Flask, render_template
from apex_legends_api import ApexLegendsAPI, ALPlayer, ALPlatform
from apex_legends_api.al_base import ALEventType
from apex_legends_api.al_domain import DataTracker, GameEvent
import arrow

app = Flask(__name__, template_folder='templates')
apex_api: ApexLegendsAPI = ApexLegendsAPI(api_key='Mr9btAmjuEw9wmFQcoPW')
player1: ALPlayer = apex_api.get_player(name='TTVKn0cktane', platform=ALPlatform.XBOX)
player2: ALPlayer = apex_api.get_player(name='TTV H0l0rage', platform=ALPlatform.XBOX)


@app.route('/')
def hello_world():
    """ Simple bootstrapped HELLO route """
    # line = create_plot()
    bar = create_bar(player1, player2)
    return render_template('index.html', player=player1, plot=bar)


def create_bar(player_one, player_two):
    p1_damage_day: dict = dict()
    p1_game_day: dict = dict()
    p2_damage_day: dict = dict()
    p2_game_day: dict = dict()
    for match in player_one.events:
        if match.event_type == ALEventType.GAME:
            match.__class__ = GameEvent
            day_key = str(arrow.get(match.timestamp).to('US/Pacific').floor('day'))
            if day_key not in p1_damage_day:
                p1_damage_day[day_key] = 0
                p1_game_day[day_key] = 0
            tracker: DataTracker
            for tracker in match.game_data_trackers:
                if tracker.key == 'damage' or tracker.key == 'specialEvent_damage':
                    p1_damage_day[day_key] += int(tracker.value)
                    p1_game_day[day_key] += 1

    for match in player_two.events:
        if match.event_type == ALEventType.GAME:
            match.__class__ = GameEvent
            day_key = str(arrow.get(match.timestamp).to('US/Pacific').floor('day'))
            if day_key not in p2_damage_day:
                p2_damage_day[day_key] = 0
                p2_game_day[day_key] = 0
            tracker: DataTracker
            for tracker in match.game_data_trackers:
                if tracker.key == 'damage' or tracker.key == 'specialEvent_damage':
                    p2_damage_day[day_key] += int(tracker.value)
                    p2_game_day[day_key] += 1
    p1_x_array: list = list()
    p1_y_array: list = list()
    p2_x_array: list = list()
    p2_y_array: list = list()
    for key in p1_damage_day:
        if p1_damage_day[key] > 0:
            time = arrow.get(key)
            p1_x_array.append(time.format('YYYY-MM-DD'))
            p1_y_array.append(int((p1_damage_day[key] / p1_game_day[key])))
    for key in p2_damage_day:
        if p2_damage_day[key] > 0:
            time = arrow.get(key)
            p2_x_array.append(time.format('YYYY-MM-DD'))
            p2_y_array.append(int((p2_damage_day[key] / p2_game_day[key])))

    trace1 = go.Bar(x=p1_x_array, y=p1_y_array, name=player1.global_info.name)
    trace2 = go.Bar(x=p2_x_array, y=p2_y_array, name=player2.global_info.name)
    data = [trace1, trace2]
    fig = go.Figure(data=data)
    fig.update_layout(barmode='group', title="Average Damage / game", template="plotly_dark", legend=dict(font_size=16))
    return json.dumps(fig, cls=ut.PlotlyJSONEncoder)


def create_plot():

    x = np.array([1, 2, 3, 4, 5])
    y = np.array([1, 3, 2, 3, 1])

    fig = go.Figure()
    # noinspection PyTypeChecker
    fig.add_trace(go.Scatter(x=x, y=y + 5, name="spline",
                             text=["tweak line smoothness<br>with 'smoothing' in line object"],
                             hoverinfo='text+name',
                             line_shape='spline'))
    fig.update_traces(hoverinfo='text+name', mode='lines+markers')
    fig.update_layout(template="plotly_dark", legend=dict(y=0.5, traceorder='reversed', font_size=16))
    return json.dumps(fig, cls=ut.PlotlyJSONEncoder)


if __name__ == '__main__':
    app.run()
