""" Dataclass to represent tracker_info collection """
from dataclasses import dataclass
from typing import List
from pymongo.collection import Collection

from mashumaro import DataClassDictMixin


@dataclass
class TrackerInfo (DataClassDictMixin):
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
    def __init__(self, collection: Collection):
        self._collection = collection
        self._tracker_info_collection: List[TrackerInfo] = list()

    @property
    def tracker_info_collection(self) -> List[TrackerInfo]:
        """ Lazy init for tracker info """
        if not self._tracker_info_collection:
            self._tracker_info_collection: List[TrackerInfo] = list()
            for item in self._collection.find({}):
                self._tracker_info_collection.append(TrackerInfo.from_dict(item))
        return self._tracker_info_collection

    def category_for_key(self, key: str) -> str:
        """ Returns the category for the key """
        for tracker in self.tracker_info_collection:
            if tracker.tracker_key == key:
                return tracker.category
        return key
