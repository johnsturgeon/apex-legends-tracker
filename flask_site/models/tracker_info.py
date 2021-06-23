""" Dataclass to represent tracker_info collection """
from typing import List

from pydantic import BaseModel


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
    def __init__(self, tracker_info_data: dict):
        self.tracker_info_list: List[TrackerInfo] = list()
        tracker: dict
        for tracker in tracker_info_data['trackers']:
            self.tracker_info_list.append(TrackerInfo(**tracker))

    def category_for_key(self, key: str) -> str:
        """ Returns the category for the key """
        for tracker in self.tracker_info_list:
            if tracker.tracker_key == key:
                return tracker.category
        return key
