""" customize settings for all scripts run in the interpreter """
import os
import site
# site.addsitedir(os.path.join(os.path.dirname(__file__), 'bin'))
site.addsitedir(os.path.join(os.path.dirname(__file__), 'flask_site'))
