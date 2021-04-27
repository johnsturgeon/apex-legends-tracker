""" Module uses plotly to create JSON for graphs usable by the ploltly javascript libs """
import json
import plotly.graph_objects as go
import plotly.utils as ut
import numpy as np
from apex_legends_api import ALPlayer
from apex_stats import PlayerData


def create_bar_trace(player: ALPlayer, category: str) -> go.Bar:
    """ Creates a bar trace for a plotly bar graph """
    player_data = PlayerData(player)
    x_array, y_array = player_data.data_for_category_day_average(category)

    return go.Bar(x=x_array, y=y_array, name=player.global_info.name)


def create_bar(player_one, category: str):
    """ Create bar chart for two player comparison """
    p1_trace = create_bar_trace(player_one, category)
    data = [p1_trace]
    fig = go.Figure(data=data)
    fig.update_layout(
        barmode='group',
        title="Average Damage / game",
        template="plotly_dark",
        legend=dict(font_size=16)
    )
    return json.dumps(fig, cls=ut.PlotlyJSONEncoder)


def create_plot():
    """ Create a spline smoothed chart """
    x_axis = np.array([1, 2, 3, 4, 5])
    y_axis = np.array([1, 3, 2, 3, 1])

    fig = go.Figure()
    # noinspection PyTypeChecker
    fig.add_trace(go.Scatter(x=x_axis, y=y_axis + 5, name="spline",
                             text=["tweak line smoothness<br>with 'smoothing' in line object"],
                             hoverinfo='text+name',
                             line_shape='spline'))
    fig.update_traces(hoverinfo='text+name', mode='lines+markers')
    fig.update_layout(
        template="plotly_dark", legend=dict(y=0.5, traceorder='reversed', font_size=16)
    )
    return json.dumps(fig, cls=ut.PlotlyJSONEncoder)
