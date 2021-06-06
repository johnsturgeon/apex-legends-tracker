""" Dataclass to represent basic_info collection """
from dataclasses import dataclass
from typing import List
import arrow
import desert

# pylint: disable=missing-class-docstring
import marshmallow.fields


@dataclass
class GameTracker:
    value: int
    key: str
    name: str


# pylint: disable=too-many-instance-attributes
@dataclass
class RankedGameEvent:
    uid: str
    player: str
    timestamp: int
    event: List[GameTracker]
    game_length: int = desert.field(marshmallow.fields.Integer(data_key='gameLength'))
    legend_played: str = desert.field(marshmallow.fields.String(data_key='legendPlayed'))
    current_rank_score: str = desert.field(marshmallow.fields.String(data_key='currentRankScore'))
    rank_score_change: str = desert.field(marshmallow.fields.String(data_key='rankScoreChange'))
    xp_progress: int = desert.field(marshmallow.fields.Integer(data_key='xpProgress'))
    event_type: str = desert.field(marshmallow.fields.String(data_key='eventType'))
    _day_of_event: str = None

    @property
    def day_of_event(self) -> str:
        """ Returns the 'day' of the event formatted 'YYYY-MMM-DD' (Pacific time) """
        if not self._day_of_event:
            self._day_of_event = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        return self._day_of_event
