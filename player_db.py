""" Mongo Database Wrapper for the apex-legends Player object """
from apex_legends_api import ALPlayer


class PlayerDB:
    """Instantiate this class and pass it an apex_legends Player object """
    def __init__(self, player: ALPlayer):
        self.player = player

    def mongo_data(self) -> dict:
        """ Returns all the data ready for ingestion into a mongo database """
        return {'player_uid': self.player.global_info.uid}

    def mongo_key(self) -> dict:
        """ The 'key' fields for the mongo document """
        return {'player_uid': self.player.global_info.uid}
