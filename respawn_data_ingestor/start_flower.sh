#!/bin/bash
if [[ $# -eq 0 ]] ; then
   echo "First parameter must be 'production' or 'development'"
   exit 0
fi
PID=$(ps aux | grep 'flower' | grep -v grep | grep -v start_flower | awk '{print $2}')
if [[ $PID > 0 ]] ; then
  echo "Process is running already"
  exit 1
fi
SCRIPT_PATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPT_PATH
cd ../flask_site
export PYTHONPATH=`pwd`
export FLASK_ENV=$1
cd ..
/Users/johnsturgeon/Code/apex-legends-tracker/env/bin/flower > logs/flower.out 2>&1 < /dev/null &
