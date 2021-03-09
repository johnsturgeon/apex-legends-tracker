# apex-legends-tracker
Python library for storing apex legends tracker data in a database for data analysis

## Notes
This readme will evolve with the library, it's a living document.

## Status
- [x] Setup script has been written
- [x] Setup process has been documented (here in README)

## Prerequisites
- [Tracker GG API Key](https://tracker.gg/developers/docs/getting-started)
- Mongo database 
    - Create Database: aqex_legends
    - Create a user in the `apex_legends` database to read / write the db.
    - Create empty collections: player, player_sessions (these will be populated on first run)
- Python 3.6 or greater    

## Setup
- check out this repository
- cd into `apex-legends-tracker` directory
- create a python3 virtual environment in folder called `env`
- activate the virtual environment and `pip install requirements.txt`
- run the script 'setup.py' (while still in the virtual environment)
   - You will be prompted for configuration values
