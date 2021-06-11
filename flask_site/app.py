""" Flask application for Apex Legends API Tracker """
import os
from typing import Optional, Tuple

import arrow
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, render_template, \
    abort, send_from_directory, request, session
from flask_profile import Profiler
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
from apex_utilities import get_arrow_date_to_use
from apex_view_controllers import IndexViewController, \
    DayByDayViewController, ProfileViewController, BattlePassViewController, \
    ClaimProfileViewController, DayDetailViewController
from models import Player

# timeout in seconds * minutes
seconds_in_one_day: int = 60*60*24
days_for_timeout: int = 14
COOKIE_TIME_OUT = days_for_timeout * seconds_in_one_day

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


def get_player_from_session() -> Optional[Player]:
    """ Instantiate a player from existing session data Return None if can't be found """
    if session.get('player'):
        return Player.from_dict(session.get('player'))
    return None


def save_player_to_session(player: Player):
    """ Saves the player to the session """
    session['player'] = player.to_dict()


def get_player_from_cookie() -> Optional[Player]:
    """ Gets the player from the browser cookie """
    discord_id = request.cookies.get('discord_id')
    if discord_id:
        return apex_db_helper.player_collection.get_player_by_discord_id(int(discord_id))
    return None


def get_player_from_discord_login() -> Optional[Player]:
    """ Returns the currently logged in player, None if not logged in """
    discord_user = discord.fetch_user()
    if discord_user:
        return apex_db_helper.player_collection.get_player_by_discord_id(discord_user.id)

    return None


@app.before_request
def before_request():
    """ This runs before every single request to check for maintenance mode """
    if not get_player_from_session():
        player: Player = get_player_from_cookie()
        if player:
            save_player_to_session(player)
    if os.path.exists("maintenance"):
        abort(503)


@app.after_request
def after_request(response):
    """ Always set the cookie if it's not set """
    player: Optional[Player] = None
    if session.get('clear_discord_id'):
        response.set_cookie('discord_id', expires=0)
        session.pop('clear_discord_id')
    elif not request.cookies.get('discord_id'):
        player: Player = get_player_from_session()
        if player and player.discord_id == 0:
            player = get_player_from_discord_login()
    if player:
        response.set_cookie('discord_id', str(player.discord_id), max_age=COOKIE_TIME_OUT)

    return response


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
    player: Player = get_player_from_discord_login()
    if player is None:
        return redirect(url_for("claim_profile"))
    save_player_to_session(player)
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
        player: Player = apex_db_helper.player_collection.get_tracked_player_by_uid(int(uid))
        save_player_to_session(player)
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


@app.route('/login')
def login():
    """ create the discord session """
    return discord.create_session(scope=["identify"], prompt=False)


@app.route('/logout')
def logout():
    """ create the discord session """
    if session.get('player'):
        session.pop('player')
    session['clear_discord_id'] = "YES"
    return redirect(url_for('index'))


@app.route('/', defaults={'day': None, 'sort_key': 'name'})
@app.route('/<string:day>/', defaults={'sort_key': 'name'})
@app.route('/<string:day>/<string:sort_key>')
def index(day: str, sort_key: str):
    """ Default route """
    date_to_use = get_arrow_date_to_use(day)
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
    player, is_not_me = get_player_for_view(request.args.get('player_uid'))

    view_controller = DayByDayViewController(apex_db_helper, player=player)

    return render_template(
        'day_by_day.html',
        view_controller=view_controller,
        is_not_me=is_not_me
    )


@app.route('/day_detail')
def day_detail():
    """ route for the day_detail page """
    date_to_use = get_arrow_date_to_use(request.args.get('day'))
    player, is_not_me = get_player_for_view(request.args.get('player_uid'))

    view_controller = DayDetailViewController(apex_db_helper, player=player, day=date_to_use)

    return render_template(
        'day_detail.html',
        view_controller=view_controller,
        is_not_me=is_not_me
    )


@app.route('/profile')
def profile():
    """ Simple player profile page """
    player, is_not_me = get_player_for_view(request.args.get('player_uid'))

    view_controller = ProfileViewController(
        db_helper=apex_db_helper,
        player=player
    )
    return render_template(
        'profile.html',
        view_controller=view_controller,
        is_not_me=is_not_me
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


def get_player_for_view(player_uid: str) -> Tuple[Player, bool]:
    """
    This method will return back the player for the view.
    This will either be the player based on the given UID, or the current logged in player
    if the player_uid is None then the player MUST be logged in
    Returns:
        Player object for the target view
    """
    auth_player: Player = get_player_from_session()
    if not player_uid:
        assert auth_player
        return auth_player, False
    if auth_player and (auth_player.uid == int(player_uid)):
        return auth_player, False

    return apex_db_helper.player_collection.get_tracked_player_by_uid(int(player_uid)), True


if __name__ == '__main__':
    app.run()
