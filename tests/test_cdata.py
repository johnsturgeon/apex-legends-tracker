from models.respawn_cdata import CData
from apex_db_helper import ApexDBHelper

db_helper = ApexDBHelper()
respawn_cdata = db_helper.database.respawn_cdata


# pylint: disable=missing-function-docstring
def test_cdata_legend(cdata):
    for record in cdata:
        cdata_obj: CData = CData(db_collection=respawn_cdata, **record)
        assert cdata_obj.dict() != record
        del record['_id']
        assert cdata_obj.dict() == record

