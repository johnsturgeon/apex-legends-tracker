""" Script will run periodically and retrieve basic player data that remains unchanged. """
import time
import requests
import player_manager
from requests import exceptions
from apex_db_helper import ApexDBHelper


def save_player_data(loop_delay: int):
    """ Saves the player data record """
    try:
        player_manager.save_player_data(refresh_from_api=True)
        log.debug("Starting loop delay: %s seconds", str(LOOP_DELAY))
        # time.sleep(loop_delay)
    except exceptions.ConnectionError as error_message:
        log.error(error_message)


if __name__ == "__main__":

    log = ApexDBHelper().logger
    MIN_LOOP_DELAY = 5
    MAX_LOOP_DELAY = 50
    LOOP_DELAY: int = MIN_LOOP_DELAY if player_manager.is_anyone_online() else MAX_LOOP_DELAY
    PREVIOUS_LOOP_DELAY = LOOP_DELAY
    log.info("Starting up the monitor")
    while True:
        try:
            requests.get("https://hc-ping.com/ac0f2dc2-5075-4a79-b644-16218967a293", timeout=10)
        except requests.RequestException as error:
            # Log ping failure here...
            log.error("Ping of healthchecks.io failed: %s", error)
        save_player_data(LOOP_DELAY)

        LOOP_DELAY = MIN_LOOP_DELAY if player_manager.is_anyone_online() else MAX_LOOP_DELAY
        if PREVIOUS_LOOP_DELAY != LOOP_DELAY:
            log.info("Changing Loop delay to %s", str(LOOP_DELAY))
        PREVIOUS_LOOP_DELAY = LOOP_DELAY
