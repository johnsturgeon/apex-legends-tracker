from flask import Flask
from flask import Flask, render_template
from apex_legends_api import ApexLegendsAPI, ALPlayer, ALPlatform

app = Flask(__name__, template_folder='templates')
apex_api: ApexLegendsAPI = ApexLegendsAPI(api_key='Mr9btAmjuEw9wmFQcoPW')
player: ALPlayer = apex_api.get_player(name='GoshDarnedHero', platform=ALPlatform.PC)


@app.route('/')
def hello_world():
    return render_template('index.html', player=player)


if __name__ == '__main__':
    app.run()
