#!/bin/bash
###
# This script will put the site in maintenance mode, stop the DB scraper
###
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_PATH
sudo monit stop save_api_data_to_db
sudo supervisorctl restart apex-legends-tracker
rm ../flask_site/maintenance
