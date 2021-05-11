""" Flask application for Apex Legends API Tracker """
import os
from datetime import datetime
import arrow
from dotenv import load_dotenv
from flask import Flask, render_template, abort, jsonify, request
from flask_profile import Profiler
from apex_legends_api import ALPlayer
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper, ApexDBGameHelper
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


@app.route('/', defaults={'day': None})
@app.route('/<string:day>')
def index(day: str):
    """ Default route """
    if day:
        date_parts = day.split("-")
        date_to_use = arrow.get(
            datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])),
            'US/Pacific'
        )
    else:
        date_to_use = arrow.now('US/Pacific')
    starting_timestamp = date_to_use.floor('day').int_timestamp
    ending_timestamp = date_to_use.shift(days=+1).floor('day').int_timestamp
    game_helper = ApexDBGameHelper(apex_db_helper, starting_timestamp, ending_timestamp)
    return render_template(
        'index.html',
        day=day,
        game_helper=game_helper
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


@app.route('/profile/<int:player_uid>')
def profile(player_uid):
    """ Simple player profile page """
    # line = create_plot()
    if player_uid:
        player: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
        player_data: PlayerData = PlayerData(player)
        bar_plot = graphing.create_bar(player, 'damage')
        return render_template(
            'profile.html',
            player_data=player_data,
            plot=bar_plot,
            db_helper=apex_db_helper
        )

    return "Not Found"


@app.route('/profile/<int:player_uid>/<tracker_key>')
def tracker_detail(player_uid, tracker_key):
    """ Display a page for one tracker and all the detail we have for it.   """
    player: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
    player_data: PlayerData = PlayerData(player)
    return render_template(
        'tracker_detail.html',
        player_data=player_data,
        tracker_key=tracker_key,
        db_helper=apex_db_helper
    )


# http://127.0.0.1:5000/_get_tracker_data?player_uid=2533274947905327&tracker_key=wins
# Json functions
@app.route('/_get_tracker_data')
def get_tracker_data():
    """ Ajax query to get player data """
    player_uid = request.args.get('player_uid', 0, type=int)
    tracker_key = request.args.get('tracker_key', 0, type=str)
    # legend_name = request.args.get('legend_name', 0, type=str)
    player_totals = apex_db_helper.get_player_totals(
        uid=player_uid, tracker_keys=[tracker_key], active_legends_only=True
    )
    tracker_totals = player_totals[tracker_key]
    # total = tracker_totals['total']
    # count = tracker_totals[legend_name]['total']
    # legend_state: TrackerDataState = tracker_totals[legend_name]['tracker_state']
    # global_state: TrackerDataState = tracker_totals['tracker_state']
    response = {
        'tracker_key': tracker_key,
        'tracker_totals': tracker_totals,
    }
    json_response = jsonify(response)
    return json_response


@app.template_filter('append_version_number')
def append_version_number(value):
    """Jinja filter returns the current version """
    return f"{value}{os.getenv('VERSION')}"


if __name__ == '__main__':
    app.run()
