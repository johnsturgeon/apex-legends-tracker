# apex-legends-tracker
This is a flask website you can host.  It will allow you to query the apexlegendsapi.com
(provided you get a key), and save data for analysis, and fun in your own MongoDB.

See: https://github.com/johnsturgeon/apex-legends-tracker/wiki for more information

## Prerequisites
- [Apex Legends API Key](https://apexlegendsapi.com)
- Python 3.6 or greater    

## Setup
- check out this repository
- cd into `apex-legends-tracker` directory
- create a python3 virtual environment in folder called `env`
- enter the virtual environment `source env/bin/activate`
- upgrade pip `pip install --upgrade pip`
- activate the virtual environment and `pip install -r requirements.txt`
- if you plan on doing development work, you should run `pip install dev_requirements.txt` as well
- run the configuration script `python config_setup/configure.py` (while still in the virtual environment)
   - You will be prompted for configuration values

## Running
- after entering prompts you can run the flask site:
  - `cd flask_site`
  - `flask run`

