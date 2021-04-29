""" Passenger WSGI used when we're in maintenance mode """


def application(_, start_response):
    """ default route if we're in maintenance mode"""
    start_response('200 OK', [('Content-type', 'text/html')])
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
            <a href="mailto:goshdarnedhero@icloud.com">goshdarnedhero@icloud.com</a>.
            We'll be back up soon!
        </p>
        <p>&mdash; (You can play some Apex Legends while you wait!)</p>
        </div>
        </div>
    </body>
    </html>
    """]
