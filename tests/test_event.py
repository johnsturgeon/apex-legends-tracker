""" event model tests """
from models.event import GameEvent, LevelEvent, RankEvent, SessionEvent


# pylint: disable=missing-function-docstring
def test_game_from_list(game_event_list):
    for game in game_event_list:
        game_event: GameEvent = GameEvent(**game)
        assert game_event.dict() != game
        del game['_id']
        assert game_event.dict() == game
        game_event.kills = 2
        assert game_event.dict() == game


def test_level_from_list(level_event_list):
    for level in level_event_list:
        level_event: LevelEvent = LevelEvent(**level)
        assert level_event.dict() != level
        del level['_id']
        assert level_event.dict() == level


def test_rank_from_list(rank_event_list):
    for rank in rank_event_list:
        rank_event: RankEvent = RankEvent(**rank)
        assert rank_event.dict() != rank
        del rank['_id']
        assert rank_event.dict() == rank


def test_session_from_list(session_event_list):
    for session in session_event_list:
        session_event: SessionEvent = SessionEvent(**session)
        assert session_event.dict() != session
        del session['_id']
        assert session_event.dict() == session
