""" Dataclass to represent respawn season collection """
from __future__ import annotations

import os
from enum import Enum
from typing import List, Optional, Tuple
from uuid import uuid4

import arrow
from pymongo.collection import Collection

# pylint: disable=import-error
from base_db_model import BaseDBModel
from instance.config import get_config
from models import RespawnRecord

config = get_config(os.getenv('FLASK_ENV'))


class SeasonInvalidSplitNumber(Exception):
    pass


class RespawnSeason(BaseDBModel):
    season_number: int
    start_date: str
    end_date: str
    ranked_split_date: Optional[str] = None

    def dict(self, **kwargs):
        return super().dict(
            exclude_none=True,
            **kwargs
        )

    @property
    def db_key(self) -> dict:
        return {
            'season_number': self.season_number
        }

    @property
    def first_ranked_split_dates(self) -> Tuple[str, str]:
        """
        Get the start_end dates for the first ranked split
        Returns:
            (start_date, end_date) formatted 'YYYY-MM-DD'
        """
        start_date = self.start_date
        end_date = arrow.get(self.ranked_split_date).shift(days=-1).format('YYYY-MM-DD')
        return start_date, end_date

    @property
    def second_ranked_split_dates(self) -> Tuple[str, str]:
        """
        Get the start_end dates for the second ranked split
        Returns:
            (start_date, end_date) formatted 'YYYY-MM-DD'
        """
        return self.ranked_split_date, self.end_date

    def get_ranked_split_dates(self, split_number: int) -> Tuple[str, str]:
        """
        Returns the ranked split dates for split number 1 or 2
        Args:
            split_number (): MUST be 1 or 2

        Returns:
            start_date, end_date
        """
        if split_number not in [1, 2]:
            raise SeasonInvalidSplitNumber
        if split_number == 1:
            return self.first_ranked_split_dates
        return self.second_ranked_split_dates


def clean_up_respawn_season_db():
    """ Go through all the records that don't have UUID's and add them """
    from apex_db_helper import ApexDBHelper

    collection: Collection = ApexDBHelper().database.respawn_season
    count: int = 1
    for record in collection.find({'uuid': {'$exists': False}}):
        if not record.get('uuid'):
            print(f"Updating UUID: {count}")
            count += 1
            record['uuid'] = uuid4()
            collection.update_one(
                filter={'season_number': record['season_number']},
                update={"$set": record}
            )


if __name__ == '__main__':
    clean_up_respawn_season_db()
