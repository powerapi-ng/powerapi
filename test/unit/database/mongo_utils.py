"""
function used to load/drop data on mongoDB database during testing
"""
import datetime
import pymongo


def generate_hwpc_report(report_id, sensor, target):
    """ generate a HWPC report with json format
    """
    return {
        '_id': str(report_id),
        'timestamp': str(datetime.datetime.now()),
        'sensor': str(sensor),
        'target': str(target),
        'groups': {
            'megagroup': {
                '0': {
                    '0': {
                        'event1': 100,
                        'event2': 200
                    }
                }
            }
        }
    }


def generate_colection(db, name, capped, item_generator, size=None):
    """
    generate a collection and fill it

    :param db: the database to insert the collectio
    :param str name: name of the collection
    :param boolean capped: True if the collection must be capped, in this case,
                           the size parameter must be set
    :param item_generator: generator that generate items to be stored on the
                           collection
    :param int size: (in case capped is set to True) max size of the collection
    """
    # delete collection if it already exist
    db[name].drop()

    # create collection
    if capped:
        db.create_collection(name, capped=True, size=size)
    else:
        db.create_collection(name)

    for item in item_generator():
        db[name].insert_one(item)


def make_generator_unit_mongo(nb_items):
    """
    Generate *nb_items* HWPCReport
    """
    def generator():
        for i in range(nb_items):
            yield generate_hwpc_report(i, 'sensor_test', 'system')
    return generator


def gen_base_test_unit_mongo(hostname, port):
    """
    create a database that will be used by mongodb unit test
    """
    mongo = pymongo.MongoClient(hostname, port)
    db = mongo['test_mongodb']

    generate_colection(db, 'test_mongodb1', False,
                       make_generator_unit_mongo(10))
    generate_colection(db, 'test_mongodb2', True,
                       make_generator_unit_mongo(10), size=(256 * 40))
    generate_colection(db, 'test_mongodb3', False,
                       make_generator_unit_mongo(2))
    mongo.close()


def clean_base_test_unit_mongo(hostname, port):
    """
    drop test_mongodb1, test_mongodb2 and test_mongodb3 collections
    """
    mongo = pymongo.MongoClient(hostname, port)
    db = mongo['test_mongodb']
    for col_name in ['test_mongodb1', 'test_mongodb2', 'test_mongodb3']:
        db[col_name].drop()
    mongo.close()


def make_generator_unit_filter(sensor_names):
    def generator():
        for n in range(len(sensor_names)):
            for i in range(2):
                yield generate_hwpc_report(n * 2 + i, sensor_names[n], 'system')
    return generator


def gen_base_test_unit_filter(hostname, port):
    """
    create a database that will be used by filter unit test
    """
    mongo = pymongo.MongoClient(hostname, port)
    db = mongo['test_filter']
    generate_colection(db, 'test_filter1', False, make_generator_unit_filter(
        ["sensor_test1", "sensor_test2", "sensor_test3"]))
    mongo.close()


def clean_base_test_unit_filter(hostname, port):
    """
    drop test_filter1 collection
    """
    mongo = pymongo.MongoClient(hostname, port)
    db = mongo['test_filter']
    db['test_filter1'].drop()
    mongo.close()
