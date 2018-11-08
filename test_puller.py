"""
Module test db
"""

from smartwatts.database.csvdb import CsvDB
from smartwatts.database.mongodb import MongoDB
from smartwatts.report import HWPCReport
from smartwatts.filter import HWPCFilter
from smartwatts.puller import ActorPuller
from smartwatts.actor import Actor
import json
import zmq


class UselessMessage:
    pass


class ActorTest(Actor):
    def __init__(self, name, verbose=False):
        Actor.__init__(self, name, verbose)

    def init_actor(self):
        return

    def initial_receive(self, msg):
        self.log("NOUVEAU MSG")


def main():
    """ Main """
    mongodb = MongoDB("localhost", 27017, "smartwatts", "sensor")
    #csvdb = CsvDB(['/home/jordan/git/smartwatts/data/core',
    #               '/home/jordan/git/smartwatts/data/pcu',
    #               '/home/jordan/git/smartwatts/data/rapl'])
    #csvdb.load()

    act = ActorTest('test', verbose=True)
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, act)
    puller = ActorPuller('puller', mongodb, hwpc_filter, verbose=True, timeout=1000)

    context = zmq.Context()
    puller.connect(context)

    for _ in range(10):
        puller.send(UselessMessage())

    act.start()
    puller.start()

    act.join()
    puller.join()


main()
