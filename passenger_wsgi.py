""" Passenger WSGI is a wrapper for the app to be deployed in a WSGI environment """
import sys
import os
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
INTERP = APP_ROOT + "/env/bin/python"
# INTERP is present twice so that the new Python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.insert(0, APP_ROOT + '/flask_site/')
# pylint: disable-all
from app import app as application
