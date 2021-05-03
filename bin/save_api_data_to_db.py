""" Script will run periodically and retrieve basic player data that remains unchanged. """
import time
import arrow
import requests
import player_manager
from requests import exceptions


def save_player_data():
    """ Saves the player data record """
    print(f"{arrow.now().format()}: Getting api data: ")
    seconds = 50
    try:
        player_manager.save_player_data()
        if player_manager.is_anyone_online():
            seconds = 5
        print(f"{arrow.now().format()}: Saved api data:  waiting {seconds} seconds")
        time.sleep(seconds)
    except exceptions.ConnectionError as error_message:
        print(error_message)


if __name__ == "__main__":
    while True:
        try:
            requests.get("https://hc-ping.com/ac0f2dc2-5075-4a79-b644-16218967a293", timeout=10)
        except requests.RequestException as error:
            # Log ping failure here...
            print("Ping failed: %s" % error)
        save_player_data()
