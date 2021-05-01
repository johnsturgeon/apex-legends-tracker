""" Script will run periodically and retrieve basic player data that remains unchanged. """
import time
import player_manager
from requests import exceptions

while True:
    try:
        print("Looking for Player Data to save:")
        player_manager.save_player_data(refresh_from_api=True)
        print("Looking for Event Data to save:")
        player_manager.save_event_data(refresh_from_api=True)
        SECONDS = 0
        for i in range(SECONDS):
            print("", end="\r")
            print("[", end="")
            for _ in range(i):
                print("•", end="")
            for _ in range(SECONDS-i):
                print(".", end="")
            print("]", end="")
            time.sleep(1)
        print("", end="\r")
        print("looping...")
    except exceptions.ConnectionError as error:
        print(error)
