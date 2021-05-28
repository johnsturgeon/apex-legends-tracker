""" Flask application for Apex Legends API Tracker """
import os
from datetime import datetime
import arrow
from dotenv import load_dotenv
from flask import Flask, render_template, abort, send_from_directory
from flask_profile import Profiler
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_view_controllers import IndexViewController,\
    DayByDayViewController, ProfileViewController, BattlePassViewController

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


@app.route('/apple-touch-icon.png')
def favicon():
    """ route for favicon """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'images/favicons/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/', defaults={'day': None, 'sort_key': 'name'})
@app.route('/<string:day>/', defaults={'sort_key': 'name'})
@app.route('/<string:day>/<string:sort_key>')
def index(day: str, sort_key: str):
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
    index_view_controller = IndexViewController(
        apex_db_helper, starting_timestamp, ending_timestamp
    )
    if not day:
        day = date_to_use.format('YYYY-MM-DD')
    prev_day = date_to_use.shift(days=-1).format('YYYY-MM-DD')
    today = arrow.now('US/Pacific')
    next_day = None
    if date_to_use < today.shift(days=-1):
        next_day = date_to_use.shift(days=+1).format('YYYY-MM-DD')
    return render_template(
        'index.html',
        day=day,
        prev_day=prev_day,
        next_day=next_day,
        index_view_controller=index_view_controller,
        sort_key=sort_key
    )


@app.route('/day_by_day/<int:player_uid>')
def day_by_day(player_uid: int):
    """ List of player matches and some detail / day """
    view_controller = DayByDayViewController(apex_db_helper, player_uid=player_uid)

    return render_template(
        'day_by_day.html',
        view_controller=view_controller
    )


@app.route('/profile/<int:player_uid>')
def profile(player_uid):
    """ Simple player profile page """
    # line = create_plot()
    if player_uid:
        view_controller = ProfileViewController(
            db_helper=apex_db_helper,
            player_uid=player_uid
        )
        return render_template(
            'profile.html',
            view_controller=view_controller
        )

    return "Not Found"


@app.route('/battlepass/')
def battlepass():
    """ Battle pass page """
    view_controller = BattlePassViewController(db_helper=apex_db_helper)
    return render_template(
        'battlepass.html',
        view_controller=view_controller
    )


@app.template_filter('append_version_number')
def append_version_number(value):
    """Jinja filter returns the current version """
    return f"{value}{os.getenv('VERSION')}"


if __name__ == '__main__':
    app.run()
