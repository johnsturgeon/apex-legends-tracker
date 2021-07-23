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

    if key.startswith('gcard_tracker_'):
        return_category = CDataCategory.TRACKER
    if key.startswith('character_intro_quip_'):
        return_category = CDataCategory.INTRO_QUIP
    if key.startswith('gcard_badge_'):
        return_category = CDataCategory.BADGE
    if key.startswith('character_skin_'):
        return_category = CDataCategory.CHARACTER_SKIN
    if key.startswith('gcard_frame_'):
        return_category = CDataCategory.CHARACTER_FRAME
    if key.startswith('gcard_stance_'):
        return_category = CDataCategory.CHARACTER_STANCE
    if key.startswith('character_'):
        return_category = CDataCategory.CHARACTER

    return return_category


def get_tracker_grouping(key: str) -> CDataTrackerGrouping:
    """ Returns the grouping for a given tracker key """
    return_grouping: CDataTrackerGrouping = CDataTrackerGrouping.UNGROUPED
    if '_kills' in key:
        return_grouping = CDataTrackerGrouping.KILLS
    if '_damage' in key:
        return_grouping = CDataTrackerGrouping.DAMAGE
    if key.endswith('_win') or \
            key.endswith('_wins') or \
            '_win_' in key or \
            '_wins_' in key:
        return_grouping = CDataTrackerGrouping.WINS
    if key.endswith('_headshots'):
        return_grouping = CDataTrackerGrouping.HEADSHOTS
    if key.endswith('_executions'):
        return_grouping = CDataTrackerGrouping.EXECUTIONS
    if key.endswith('_revives'):
        return_grouping = CDataTrackerGrouping.REVIVES
    if key.endswith('_games_played'):
        return_grouping = CDataTrackerGrouping.GAMES_PLAYED
    if key.endswith('_top_3'):
        return_grouping = CDataTrackerGrouping.TOP_3

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

    if "_bangalore_" in key:
        return_legend = RespawnLegend.BANGALORE
    if "_bloodhound_" in key:
        return_legend = RespawnLegend.BLOODHOUND
    if "_caustic_" in key:
        return_legend = RespawnLegend.CAUSTIC
    if "_crypto_" in key:
        return_legend = RespawnLegend.CRYPTO
    if "_fuse_" in key:
        return_legend = RespawnLegend.FUSE
    if "_gibraltar_" in key:
        return_legend = RespawnLegend.GIBRALTAR
    if "_horizon_" in key:
        return_legend = RespawnLegend.HORIZON
    if "_lifeline_" in key:
        return_legend = RespawnLegend.LIFELINE
    if "_loba_" in key:
        return_legend = RespawnLegend.LOBA
    if "_mirage_" in key:
        return_legend = RespawnLegend.MIRAGE
    if "_octane_" in key:
        return_legend = RespawnLegend.OCTANE
    if "_pathfinder_" in key:
        return_legend = RespawnLegend.PATHFINDER
    if "_rampart_" in key:
        return_legend = RespawnLegend.RAMPART
    if "_revenant_" in key:
        return_legend = RespawnLegend.REVENANT
    if "_seer_" in key:
        return_legend = RespawnLegend.SEER
    if "_valkyrie_" in key:
        return_legend = RespawnLegend.VALKYRIE
    if "_wattson_" in key:
        return_legend = RespawnLegend.WATTSON
    if "_wraith_" in key:
        return_legend = RespawnLegend.WRAITH
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
