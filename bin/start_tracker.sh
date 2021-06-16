#!/bin/bash
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_PATH
cd ../flask_site
export PYTHONPATH=`pwd`
cd ..
nohup env/bin/python ${SCRIPT_PATH}/save_api_data_to_db.py > nohup.out 2> nohup.err < /dev/null &
