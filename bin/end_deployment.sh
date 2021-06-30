#!/bin/bash
###
# This script will put the site in maintenance mode, stop the DB scraper
###
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
sudo monit start save_api_data_to_db
$SCRIPT_PATH/start_ingestion.sh
sudo supervisorctl restart apex-legends-tracker
rm $SCRIPT_PATH/../maintenance
