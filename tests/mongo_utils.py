"""
Copyright (c) 2018, INRIA
Copyright (c) 2018, University of Lille
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import datetime
import pymongo


def generate_hwpc_report(report_id, sensor, target, timestamp=[0]):
    """ generate a HWPC report with json format
    """
    timestamp[0] += 1
    return {
        '_id': str(report_id),
        'timestamp': datetime.datetime.fromtimestamp(timestamp[0]),
        'sensor': str(sensor),
        'target': str(target),
        'groups': {
            'rapl': {
                '0': {
                    '0': {
                        'RAPL_EVENT': 100,
                        'simple_event': 200
                    }
                },
                '1': {
                    '0': {
                        'RAPL_EVENT': 100,
                        'simple_event': 300
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


def gen_base_test_unit_mongo(uri):
    """
    create a database that will be used by mongodb unit test
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo['test_mongodb']

    generate_colection(db, 'test_mongodb1', False,
                       make_generator_unit_mongo(10))
    generate_colection(db, 'test_mongodb2', True,
                       make_generator_unit_mongo(10), size=(256 * 40))
    generate_colection(db, 'test_mongodb3', False,
                       make_generator_unit_mongo(2))
    mongo.close()


def clean_base_test_unit_mongo(uri):
    """
    drop test_mongodb1, test_mongodb2 and test_mongodb3 collections
    """
    mongo = pymongo.MongoClient(uri)
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


def gen_base_test_unit_filter(uri):
    """
    create a database that will be used by filter unit test
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo['test_filter']
    generate_colection(db, 'test_filter1', False, make_generator_unit_filter(
        ["sensor_test1", "sensor_test2", "sensor_test3"]))
    mongo.close()


def clean_base_test_unit_filter(uri):
    """
    drop test_filter1 collection
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo['test_filter']
    db['test_filter1'].drop()
    mongo.close()


def gen_base_db_test(uri, nb_items):
    """
    Generate a mongoDB database named MongoDB1 containing *nb_items* HWPC report
    in the test_hwrep collection
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo['MongoDB1']
    generate_colection(db, 'test_hwrep', False,
                       make_generator_unit_mongo(nb_items))
    mongo.close()


def clean_base_db_test(uri):
    """
    drop test_hwrep and test_result collections
    """
    mongo = pymongo.MongoClient(uri)
    db = mongo['MongoDB1']
    db['test_hwrep'].drop()

    db['test_result'].drop()
    mongo.close()
