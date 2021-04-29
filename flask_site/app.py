""" Flask application for Apex Legends API Tracker """
import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_profile import Profiler
from apex_legends_api import ALPlayer
from apex_api_helper import ApexAPIHelper
from apex_db_helper import ApexDBHelper
import graphing
from apex_stats import PlayerData

load_dotenv()
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


@app.route('/')
def index():
    """ Default route """
    return render_template('index.html', players=apex_db_helper.get_tracked_players())


@app.route('/days/<int:player_uid>')
def days(player_uid: int):
    """ List of player matches and some detail / day """
    player: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
    player_data: PlayerData = PlayerData(player)
    return render_template('days.html', player=player, player_data=player_data)


@app.route('/profile/<player_uid>/<category>')
def profile(player_uid=None, category="damage"):
    """ Simple player profile page """
    # line = create_plot()
    if player_uid:
        player1: ALPlayer = apex_db_helper.get_player_by_uid(uid=player_uid)
        bar_plot = graphing.create_bar(player1, category)
        return render_template('profile.html', player=player1, plot=bar_plot)

    return "Not Found"


if __name__ == '__main__':
    app.run()
