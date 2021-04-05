# apex-legends-tracker
This is a flask website you can host.  It will allow you to query the apexlegendsapi.com
(provided you get a key), and save data for analysis, and fun in your own MongoDB.

See: https://github.com/johnsturgeon/apex-legends-tracker/wiki for more information

## Prerequisites
- [Apex Legends API Key](https://apexlegendsapi.com)
- Mongo database 
    - Create Database: aqex_legends
    - Create a user in the `apex_legends` database to read / write the db.
    - Create empty collections: player, player_events (these will be populated on first run)
      (You won't have to do this once #16 has been implemented)
- Python 3.6 or greater    

## Setup
- check out this repository
- cd into `apex-legends-tracker` directory
- create a python3 virtual environment in folder called `env`
- activate the virtual environment and `pip install requirements.txt`
- run the script 'setup.py' (while still in the virtual environment)
   - You will be prompted for configuration values
  
## Running

