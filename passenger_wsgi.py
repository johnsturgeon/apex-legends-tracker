""" Passenger WSGI is a wrapper for the app to be deployed in a WSGI environment """
import sys
import os
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if os.path.isfile(APP_ROOT + 'maintenance.txt'):
    def application(_, start_response):
        """ default route if we're in maintenance mode"""
        start_response('200 OK', [('Content-type', 'text/plain')])
        return ["""
        <!DOCTYPE html>
         <html>
         <head>
            <meta http-equiv="Content-type" content="text/html;charset=UTF-8">
            <title>Performing Maintenance</title>
            <style type="text/css">
                body { text-align: center; padding: 150px; }
                h1 { font-size: 40px; }
                body { font: 20px Helvetica, sans-serif; color: #333; }
                #article { display: block; text-align: left; width: 650px; margin: 0 auto; }
                a { color: #dc8100; text-decoration: none; }
                a:hover { color: #333; text-decoration: none; }
            </style>
        </head>
        <body>
            <div id="article">
                <h1>Our site is getting a little tune up and some love.</h1>
            <div>
            <p>
                We apologize for the inconvenience, but we're performing some maintenance.
                You can contact me at
                <a href="mailto:john.sturgeon@me.com">john.sturgeon@me.com</a>.
                We'll be back up soon!
            </p>
            <p>&mdash; (You can play some Apex Legends while you wait!)</p>
            </div>
            </div>
        </body>
        </html>
        """]
INTERP = APP_ROOT + "/env/bin/python"
# INTERP is present twice so that the new Python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)
sys.path.insert(0, APP_ROOT + '/flask_site/')
