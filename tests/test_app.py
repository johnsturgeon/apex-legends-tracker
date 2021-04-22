""" Unit test for the flask app """
from flask_site import app


def test_index():
    """ Basic test just to make sure the site works """
    response = app.app.test_client().get('/')
    assert response.status_code == 200
    assert 'GoshDarnedHero' in str(response.data)
