""" blah """
import os
from dotenv import load_dotenv

from pymongo import MongoClient
import pymongo.database
from bson import ObjectId
from pymongo.collection import Collection

load_dotenv()


def copy_db():
    """ blah 2 """
    source_uri = f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}"
    source_uri += f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
    source_uri += "?retryWrites=true&w=majority"
    source_client: MongoClient = MongoClient(source_uri)
    source_database: pymongo.database.Database = source_client.apex_legends

    dest_client: MongoClient = MongoClient(
        host='208.113.129.246',
        username='apex_admin',
        password='U3ucUK-hofzGh',
        authSource='apex_legends'
    )
    dest_database: pymongo.database.Database = dest_client.apex_legends

    source_basic_info_db: Collection = source_database.basic_info
    dest_basic_info_db: Collection = dest_database.basic_info
    for document in source_basic_info_db.find({}):
        dest_basic_info_db.update_one(
            filter={"_id": document["_id"]}, update={"$set": document}, upsert=True
        )

    source_basic_player_db: Collection = source_database.basic_player
    dest_basic_player_db: Collection = dest_database.basic_player
    for document in source_basic_player_db.find(
            {
                "_id": {
                    "$gt": ObjectId("60c6f8f4c13000fb9ee4f58c")
                }
            }
    ):
        dest_basic_player_db.update_one(
            filter={"_id": document["_id"]}, update={"$set": document}, upsert=True)

    source_event_db: Collection = source_database.event
    dest_event_db: Collection = dest_database.event
    for document in source_event_db.find(
                {
                    "_id": {
                        "$gt": ObjectId("60c6f8f64d20cc281469555e")
                    }
                }
    ):
        dest_event_db.update_one(
         filter={"_id": document["_id"]}, update={"$set": document}, upsert=True
        )

    source_player_db: Collection = source_database.player
    dest_player_db: Collection = dest_database.player
    for document in source_player_db.find({}):
        dest_player_db.update_one(
            filter={"_id": document["_id"]}, update={"$set": document}, upsert=True
        )

    source_tracker_info_db: Collection = source_database.tracker_info
    dest_tracker_info_db: Collection = dest_database.tracker_info
    for document in source_tracker_info_db.find({}):
        dest_tracker_info_db.update_one(
            filter={"_id": document["_id"]}, update={"$set": document}, upsert=True
        )


if __name__ == "__main__":
    copy_db()
    # apex_db_helper.event_collection.delete_many({'eventType': 'rankScoreChange'})
