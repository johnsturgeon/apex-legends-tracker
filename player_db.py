""" Mongo Database Wrapper for the apex-legends Player object """
from apex_legends.domain import Player
from apex_legends.domain import Session


class PlayerDB:
    """Instantiate this class and pass it an apex_legends Player object """
    def __init__(self, player: Player):
        self.player = player
        self.user_name = player.username
        assert hasattr(player, 'matchesplayed')
        self.matches_played = player.matchesplayed

    def sessions(self) -> list[Session]:
        """ Returns a list of the player session objects"""
        return self.player.sessions

    @property
    def data(self) -> dict:
        """ return all the raw player data in 'dict' format """
        # noinspection Pylint, PyProtectedMember
        return self.player._data

    def mongo_data(self) -> object:
        """ Returns all the data ready for ingestion into a mongo database """
        return {
            'user_name': self.user_name,
            'matches_played': self.matches_played,
            '_data': self.data
        }

    def mongo_key(self):
        """ The 'key' fields for the mongo document """
        return {
            'user_name': self.user_name,
            'matches_played': self.matches_played
        }
