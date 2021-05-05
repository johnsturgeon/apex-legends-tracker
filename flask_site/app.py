""" Flask application for Apex Legends API Tracker """
import os

import arrow
from dotenv import load_dotenv
from flask import Flask, render_template, abort
from flask_profile import Profiler
from apex_legends_api import ALPlayer
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
import graphing
from apex_stats import PlayerData

load_dotenv()
load_dotenv('common.env')
app = Flask(__name__, template_folder='templates')
api_key = os.getenv('APEX_LEGENDS_API_KEY')
default_player = os.getenv('DEFAULT_PLAYER_NAME')
apex_api_helper = ApexAPIHelper()
apex_db_helper = ApexDBHelper()
Profiler(app)
app.config["flask_profiler"] = {
    "storage": {
        "engine": "mongodb",
    },
    "profile_dir": "/Users/johnsturgeon/Code/apex-legends-tracker/log"
}


@app.before_request
def before_request():
    """ This runs before every single request to check for maintenance mode """
    if os.path.exists("maintenance"):
        abort(503)


@app.errorhandler(503)
def under_maintenance(_):
    """ Render the default maintenance page """
    return render_template('503.html'), 503


@app.route('/', defaults={'day': arrow.now().format("YYYY-MM-DD")})
@app.route('/<string:day>')
def index(day: str = arrow.now().format('YYYY-MM-DD')):
    """ Default route """
    tracked_players = apex_db_helper.get_tracked_players()
    player_data_dict: dict = {}
    for player in tracked_players:
        db_player: ALPlayer = apex_db_helper.get_player_by_uid(player['uid'])
        player_data_dict[player['name']] = PlayerData(db_player)
    return render_template(
        'index.html',
        day=day,
        arrow=arrow,
        players=apex_db_helper.get_tracked_players(),
        player_data_dict=player_data_dict,
        db_helper=apex_db_helper
    )


@app.route('/days/<int:player_uid>')
def days(player_uid: int):
    """ List of player matches and some detail / day """
    player: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
    player_data: PlayerData = PlayerData(player)
    return render_template(
        'days.html',
        player=player,
        player_data=player_data,
        db_helper=apex_db_helper
    )


@app.route('/profile/<player_uid>/<category>')
def profile(player_uid=None, category="damage"):
    """ Simple player profile page """
    # line = create_plot()
    if player_uid:
        player1: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
        bar_plot = graphing.create_bar(player1, category)
        return render_template('profile.html', player=player1, plot=bar_plot)

    return "Not Found"


@app.template_filter('append_version_number')
def append_version_number(value):
    """Jinja filter returns the current version """
    return f"{value}: {os.getenv('VERSION')}"


if __name__ == '__main__':
    app.run()
