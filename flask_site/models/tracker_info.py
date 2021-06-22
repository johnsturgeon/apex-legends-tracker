""" Dataclass to represent tracker_info collection """
from typing import List

from pydantic import BaseModel
import pymongo.database


class TrackerInfo (BaseModel):
    """ Tracker Info Class """
    tracker_key: str
    grouping: str
    category: str
    season: str
    mode: str
    active: bool
    legend: str


class TrackerInfoCollection:
    """ Class for aggregate tracker info methods"""
    def __init__(self, db: pymongo.database.Database):
        self._collection = db.tracker_info
        self._tracker_info_list: List[TrackerInfo] = list()

    @property
    def tracker_info_collection(self) -> List[TrackerInfo]:
        """ Lazy init for tracker info """
        if not self._tracker_info_list:
            for item in self._collection.find({}):
                self._tracker_info_list.append(TrackerInfo(**item))
        return self._tracker_info_list

    def category_for_key(self, key: str) -> str:
        """ Returns the category for the key """
        for tracker in self.tracker_info_collection:
            if tracker.tracker_key == key:
                return tracker.category
        return key
