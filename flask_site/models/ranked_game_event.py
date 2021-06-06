""" Dataclass to represent basic_info collection """
from dataclasses import dataclass, field
from typing import List
import arrow

# pylint: disable=missing-class-docstring
from mashumaro import DataClassDictMixin, field_options


@dataclass
class GameTracker(DataClassDictMixin):
    value: int
    key: str
    name: str


# pylint: disable=too-many-instance-attributes
@dataclass
class RankedGameEvent(DataClassDictMixin):
    uid: str
    player: str
    timestamp: int
    event: List[GameTracker]
    game_length: int = field(metadata=field_options(alias="gameLength"))
    legend_played: str = field(metadata=field_options(alias="legendPlayed"))
    current_rank_score: str = field(metadata=field_options(alias="currentRankScore"))
    rank_score_change: str = field(metadata=field_options(alias="rankScoreChange"))
    xp_progress: int = field(metadata=field_options(alias="xpProgress"))
    event_type: str = field(metadata=field_options(alias="eventType"))
    _day_of_event: str = None

    @property
    def day_of_event(self) -> str:
        """ Returns the 'day' of the event formatted 'YYYY-MMM-DD' (Pacific time) """
        if not self._day_of_event:
            self._day_of_event = arrow.get(self.timestamp).to('US/Pacific').format('YYYY-MM-DD')
        return self._day_of_event
