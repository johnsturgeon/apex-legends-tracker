from typing import Optional

import requests

from models.respawn_cdata import CDataCategory, CDataTrackerGrouping, CDataTrackerMode
from models.respawn_cdata import CData, CDataTracker
from models.respawn_record import RespawnLegend

from apex_db_helper import ApexDBHelper

db_helper = ApexDBHelper()


def get_category(key: str) -> Optional[CDataCategory]:
    if key.startswith('gcard_tracker_'):
        return CDataCategory.TRACKER
    if key.startswith('character_intro_quip_'):
        return CDataCategory.INTRO_QUIP
    if key.startswith('gcard_badge_'):
        return CDataCategory.BADGE
    if key.startswith('character_skin_'):
        return CDataCategory.CHARACTER_SKIN
    if key.startswith('gcard_frame_'):
        return CDataCategory.CHARACTER_FRAME
    if key.startswith('gcard_stance_'):
        return CDataCategory.CHARACTER_STANCE
    if key.startswith('character_'):
        return CDataCategory.CHARACTER
    else:
        return None


def get_tracker_grouping(key: str) -> CDataTrackerGrouping:
    if '_kills' in key:
        return CDataTrackerGrouping.KILLS
    if '_damage' in key:
        return CDataTrackerGrouping.DAMAGE
    if key.endswith('_win') or \
            key.endswith('_wins') or \
            '_win_' in key or \
            '_wins_' in key:
        return CDataTrackerGrouping.WINS
    if key.endswith('_headshots'):
        return CDataTrackerGrouping.HEADSHOTS
    if key.endswith('_executions'):
        return CDataTrackerGrouping.EXECUTIONS
    if key.endswith('_revives'):
        return CDataTrackerGrouping.REVIVES
    if key.endswith('_games_played'):
        return CDataTrackerGrouping.GAMES_PLAYED
    if key.endswith('_top_3'):
        return CDataTrackerGrouping.TOP_3
    return CDataTrackerGrouping.UNGROUPED


def get_tracker_mode(key: str) -> CDataTrackerMode:
    if '_arenas_' in key:
        return CDataTrackerMode.ARENAS
    else:
        return CDataTrackerMode.BATTLE_ROYALE


def get_legend(key: str) -> RespawnLegend:
    if "_bangalore_" in key:
        return RespawnLegend.BANGALORE
    if "_bloodhound_" in key:
        return RespawnLegend.BLOODHOUND
    if "_caustic_" in key:
        return RespawnLegend.CAUSTIC
    if "_crypto_" in key:
        return RespawnLegend.CRYPTO
    if "_fuse_" in key:
        return RespawnLegend.FUSE
    if "_gibraltar_" in key:
        return RespawnLegend.GIBRALTAR
    if "_horizon_" in key:
        return RespawnLegend.HORIZON
    if "_lifeline_" in key:
        return RespawnLegend.LIFELINE
    if "_loba_" in key:
        return RespawnLegend.LOBA
    if "_mirage_" in key:
        return RespawnLegend.MIRAGE
    if "_octane_" in key:
        return RespawnLegend.OCTANE
    if "_pathfinder_" in key:
        return RespawnLegend.PATHFINDER
    if "_rampart_" in key:
        return RespawnLegend.RAMPART
    if "_revenant_" in key:
        return RespawnLegend.REVENANT
    if "_valkyrie_" in key:
        return RespawnLegend.VALKYRIE
    if "_wattson_" in key:
        return RespawnLegend.WATTSON
    if "_wraith_" in key:
        return RespawnLegend.WRAITH
    return RespawnLegend.ALL


def ingest_cdata():
    """
    Ingests the cdata from
    https://github.com/r-ex/ApexKnowledge

    """

    url = "https://raw.githubusercontent.com/r-ex/ApexKnowledge/master/cdata_a.json"
    req = requests.get(url)
    if req.status_code == requests.codes.ok:
        cdata = req.json()
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
                new_record: CData = CData(db_collection=db_helper.database.respawn_cdata, **new_item)
            new_record.save()


if __name__ == '__main__':
    ingest_cdata()
