""" Flask application for Apex Legends API Tracker """
import os
from datetime import datetime
from typing import Optional

import arrow
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, render_template, \
    abort, send_from_directory, request, session
from flask_profile import Profiler
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_view_controllers import IndexViewController,\
    DayByDayViewController, ProfileViewController, BattlePassViewController,\
    ClaimProfileViewController
from models import Player

load_dotenv()
load_dotenv('common.env')
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_APP_SECRET_KEY')

# OAuth2 must make use of HTTPS in production environment.
# !! Only in development environment.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT')
app.config["DISCORD_CLIENT_ID"] = os.getenv('DISCORD_CLIENT_ID')
app.config["DISCORD_CLIENT_SECRET"] = os.getenv('DISCORD_CLIENT_SECRET')
app.config["DISCORD_REDIRECT_URI"] = os.getenv('DISCORD_REDIRECT_URI')

discord = DiscordOAuth2Session(app)

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


def logged_in_player() -> Optional[Player]:
    """ Returns the currently logged in player, None if not logged in """
    if not session.get('player'):
        discord_user = discord.fetch_user()
        player: Player = apex_db_helper.get_player_by_discord_id(discord_user.id)
        if player:
            session['player'] = player.to_dict()
            return player
    else:
        return Player.from_dict(session.get('player'))
    return None


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


@app.route("/callback")
def callback():
    """ discord callback url """
    discord.callback()
    if logged_in_player() is None:
        return redirect(url_for("claim_profile"))
    return redirect(url_for("profile"))


@app.errorhandler(Unauthorized)
def redirect_unauthorized(_):
    """ Error for unauthorized requests """
    return redirect(url_for("login"))


@app.route('/claim_profile')
@requires_authorization
def claim_profile():
    """ Page for claiming your profile """
    uid: int = request.args.get("player_uid")
    discord_user = discord.fetch_user()
    view_controller = ClaimProfileViewController(db_helper=apex_db_helper)
    if uid:
        player_uid: int = int(uid)
        view_controller.claim_profile_with_discord_id(
            player_uid=player_uid,
            discord_id=discord_user.id
        )
        return redirect(url_for('profile', player_uid=player_uid))
    return render_template(
        'claim_profile.html',
        view_controller=view_controller,
        discord_user=discord_user
    )


@app.route('/login/')
def login():
    """ create the discord session """
    return discord.create_session(scope=["identify"])


@app.route('/', defaults={'day': None, 'sort_key': 'name'})
@app.route('/<string:day>/', defaults={'sort_key': 'name'})
@app.route('/<string:day>/<string:sort_key>')
def index(day: str, sort_key: str):
    """ Default route """
    logged_in_player()
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
        sort_key=sort_key,
        logged_in_player=None
    )


@app.route('/day_by_day')
def day_by_day():
    """ List of player matches and some detail / day """
    other_player = None
    player_uid = int(request.args.get('player_uid'))
    if player_uid and logged_in_player().uid != player_uid:
        other_player = apex_db_helper.get_tracked_player_by_uid(player_uid)
    else:
        player_uid = logged_in_player().uid

    view_controller = DayByDayViewController(apex_db_helper, player_uid=player_uid)

    return render_template(
        'day_by_day.html',
        view_controller=view_controller,
        other_player=other_player
    )


@app.route('/profile')
def profile():
    """ Simple player profile page """
    other_player = None

    player_uid = request.args.get('player_uid')
    if player_uid and logged_in_player().uid != int(player_uid):
        player_uid = int(player_uid)
        other_player = apex_db_helper.get_tracked_player_by_uid(player_uid)
    else:
        player_uid = logged_in_player().uid

    view_controller = ProfileViewController(
        db_helper=apex_db_helper,
        player_uid=player_uid
    )
    return render_template(
        'profile.html',
        view_controller=view_controller,
        other_player=other_player
    )


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
