""" Flask application for Apex Legends API Tracker """
import os
from flask import Flask, render_template
from apex_legends_api import ApexLegendsAPI, ALPlayer, ALPlatform, ALAction
import flask_site.graphing as graphing
from flask_site.apex_stats import PlayerData
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, template_folder='templates')
api_key = os.getenv('APEX_LEGENDS_API_KEY')
default_player = os.getenv('DEFAULT_PLAYER_NAME')
apex_api: ApexLegendsAPI = ApexLegendsAPI(api_key=api_key)


@app.route('/')
def index():
    """ Default route """
    return render_template('index.html', players=get_players())


@app.route('/days/<player_name>')
def days(player_name=default_player):
    """ List of player matches and some detail / day """
    platform = get_platform_for_player(player_name)
    player: ALPlayer = apex_api.get_player(name=player_name, platform=platform)
    player_data: PlayerData = PlayerData(player)
    return render_template('days.html', player=player, player_data=player_data)


@app.route('/profile/<player_name>/<category>')
def profile(player_name=None, category="damage"):
    """ Simple player profile page """
    # line = create_plot()
    if player_name:
        platform = get_platform_for_player(player_name)
        player1: ALPlayer = apex_api.get_player(name=player_name, platform=platform)
        bar_plot = graphing.create_bar(player1, category)
        return render_template('profile.html', player=player1, plot=bar_plot)

    return "Not Found"


def get_platform_for_player(player: str) -> ALPlatform:
    """ Helper method that returns the platform from the given player """
    players = get_players()
    platform = ALPlatform.PC
    for tracked_player in players:
        if tracked_player["name"] == player:
            platform = ALPlatform(value=tracked_player["platform"])
    return platform


def get_players() -> list[dict]:
    """ Helper method that returns a list of players being tracked """
    first_event = apex_api.events(default_player, ALPlatform.PC, ALAction.INFO)[0]
    if not isinstance(first_event, dict):
        return list({})
    return first_event["data"]


if __name__ == '__main__':
    app.run()
