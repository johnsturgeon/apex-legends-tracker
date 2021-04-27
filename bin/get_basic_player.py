""" Script will run periodically and retrieve basic player data that remains unchanged. """
import time
import player_data
from requests import exceptions

while True:
    try:
        print("Looking for Player Data to save:")
        player_data.save_player_data()
        print("Looking for Event Data to save:")
        player_data.save_event_data()
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
