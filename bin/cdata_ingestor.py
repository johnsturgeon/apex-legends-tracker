""" Script that will ingest cdata from r-ex """
from typing import Optional

import requests

from models.respawn_cdata import CDataCategory, CDataTrackerGrouping, CDataTrackerMode
from models.respawn_cdata import CData, CDataTracker
from models.respawn_record import RespawnLegend

from apex_db_helper import ApexDBHelper

db_helper = ApexDBHelper()


def get_category(key: str) -> Optional[CDataCategory]:
    """ Returns the category for the cdata key """
    return_category: Optional[CDataCategory] = None
    categories = {
        'gcard_tracker_': CDataCategory.TRACKER,
        'character_intro_quip_': CDataCategory.INTRO_QUIP,
        'gcard_badge_': CDataCategory.BADGE,
        'character_skin_': CDataCategory.CHARACTER_SKIN,
        'gcard_frame_': CDataCategory.CHARACTER_FRAME,
        'gcard_stance_': CDataCategory.CHARACTER_STANCE,
        'character_': CDataCategory.CHARACTER
    }
    for category_key, value in categories.items():
        if key.startswith(category_key):
            return value

    return return_category


def get_tracker_grouping(key: str) -> CDataTrackerGrouping:
    """ Returns the grouping for a given tracker key """
    return_grouping: CDataTrackerGrouping = CDataTrackerGrouping.UNGROUPED

    is_in = {
        '_kills': CDataTrackerGrouping.KILLS,
        '_damage': CDataTrackerGrouping.DAMAGE,
        '_win_': CDataTrackerGrouping.WINS,
        '_wins_': CDataTrackerGrouping.WINS
    }
    for category_key, value in is_in.items():
        if category_key in key:
            return_grouping = value
    if return_grouping == CDataTrackerGrouping.UNGROUPED:
        endswith = {
            '_win': CDataTrackerGrouping.WINS,
            '_wins': CDataTrackerGrouping.WINS,
            '_headshots': CDataTrackerGrouping.HEADSHOTS,
            '_executions': CDataTrackerGrouping.EXECUTIONS,
            '_revives': CDataTrackerGrouping.REVIVES,
            '_games_played': CDataTrackerGrouping.GAMES_PLAYED,
            '_top_3': CDataTrackerGrouping.TOP_3
        }
        for category_key, value in endswith.items():
            if key.endswith(category_key):
                return_grouping = value

    return return_grouping


def get_tracker_mode(key: str) -> CDataTrackerMode:
    """ Returns tracker mode (arenas or battle royale) """
    if '_arenas_' in key:
        return CDataTrackerMode.ARENAS

    return CDataTrackerMode.BATTLE_ROYALE


# pylint: disable=too-many-branches
def get_legend(key: str) -> RespawnLegend:
    """ Returns the RespawnLegend given the key string """
    return_legend: RespawnLegend = RespawnLegend.EMPTY
    legends = {
        '_bangalore_': RespawnLegend.BANGALORE,
        '_bloodhound_': RespawnLegend.BLOODHOUND,
        '_caustic_': RespawnLegend.CAUSTIC,
        '_crypto_': RespawnLegend.CRYPTO,
        '_fuse_': RespawnLegend.FUSE,
        '_gibraltar_': RespawnLegend.GIBRALTAR,
        '_horizon_': RespawnLegend.HORIZON,
        '_lifeline_': RespawnLegend.LIFELINE,
        '_loba_': RespawnLegend.LOBA,
        '_mirage_': RespawnLegend.MIRAGE,
        '_octane_': RespawnLegend.OCTANE,
        '_pathfinder_': RespawnLegend.PATHFINDER,
        '_rampart_': RespawnLegend.RAMPART,
        '_revenant_': RespawnLegend.REVENANT,
        '_seer_': RespawnLegend.SEER,
        '_valkyrie_': RespawnLegend.VALKYRIE,
        '_wattson_': RespawnLegend.WATTSON,
        '_wraith_': RespawnLegend.WRAITH,
    }
    for legend_key, value in legends.items():
        if legend_key in key:
            return_legend = value

    return return_legend


def ingest_cdata():
    """
    Ingests the cdata from
    https://github.com/r-ex/ApexKnowledge

    """

    url = "https://raw.githubusercontent.com/r-ex/ApexKnowledge/master/cdata_a.json"
    response = requests.get(url)
    if response.ok:
        cdata = response.json()
        collection = db_helper.database.respawn_cdata
        collection.delete_many({})
        for item in cdata:
            key: str = cdata[item][1]
            name: str = cdata[item][0]
            new_item: dict = dict()
            new_item['c_data']: int = int(item)
            new_item['name']: str = name
            new_item['key']: str = key
            new_item['legend']: str = get_legend(key).value
            new_item['category']: str = get_category(key).value
            if get_category(key) == 'tracker':
                new_item['tracker_grouping']: str = get_tracker_grouping(key).value
                new_item['tracker_mode']: str = get_tracker_mode(key).value
                new_record: CDataTracker = CDataTracker(
                    db_collection=db_helper.database.respawn_cdata,
                    **new_item
                )
            else:
                new_record: CData = CData(
                    db_collection=db_helper.database.respawn_cdata, **new_item
                )
            new_record.save()


if __name__ == '__main__':
    ingest_cdata()
