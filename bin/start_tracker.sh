#!/bin/bash
PID=$(ps aux | grep 'save_api_data_to_db' | grep -v grep | awk '{print $2}')
if [[ $PID > 0 ]] ; then
  echo "Process is running already"
  exit 1
fi
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_PATH
cd ../flask_site
export PYTHONPATH=`pwd`
export FLASK_ENV='production'
cd ..
nohup env/bin/python ${SCRIPT_PATH}/save_api_data_to_db.py > logs/old_scraper.out 2> logs/old_scraper.err < /dev/null &
