""" Sets up the test database for testing (essentially copies production db) """
import os

from pymongo.errors import DuplicateKeyError

from apex_db_helper import ApexDBHelper


def main():
    """ Copies all the data from the prod db to the test db """
    os.environ['FLASK_ENV'] = "production"
    prod_db_helper = ApexDBHelper()
    os.environ['FLASK_ENV'] = "test"
    test_db_helper = ApexDBHelper()
    for collection_name in prod_db_helper.database.list_collection_names(
            filter={'type': 'collection', 'name': {'$ne': 'system.views'}}
    ):
        print(f"Checking collection: {collection_name}")
        source_collection = prod_db_helper.database[collection_name]
        dest_collection = test_db_helper.database.get_collection(collection_name)
        # if destination collection exists, get most recent record
        if dest_collection and dest_collection.count_documents({}) > 0:
            last_record = dest_collection.find().limit(1).sort([('$natural', -1)])[0]
            records = list(source_collection.find(
                {
                    "_id": {"$gte": last_record['_id']}
                }
            ))
        else:
            records = list(source_collection.find())

        collection_length: int = len(records)
        print(f"{collection_name} has {collection_length} records ")
        insert_count: int = 1
        for record in records:
            print(f"inserting record {insert_count} of {collection_length}")
            try:
                test_db_helper.database[collection_name].insert_one(record)
            except DuplicateKeyError:
                print("record already inserted")
            insert_count += 1


if __name__ == '__main__':
    main()
