#!/bin/bash
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_PATH
cd ../flask_site
export PYTHONPATH=`pwd`
export FLASK_ENV='production'
cd ..
env/bin/gunicorn app:app -b localhost:8000
