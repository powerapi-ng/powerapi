"""
smartwatts utilisation example
"""

import os
from smartwatts.pusher import PusherActor
from smartwatts.database import StdoutDB, CsvDB, MongoDB
from smartwatts.formula import TestFormulaActor
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel
from smartwatts.filter import HWPCFilter
from smartwatts.puller import PullerActor
from smartwatts.report import HWPCReport, PowerReport
from smartwatts.report_model import HWPCModel
from smartwatts.dispatcher import DispatcherActor


def log(msg):
    """ log """
    print('[' + str(os.getpid()) + '] ' + msg)


log('I\'m main')


def main():
    """ main """

    # Pusher
    mongodb = MongoDB(PowerReport, 'localhost', 27017, 'smartwatts', 'save', save_mode=True)
    pusher = PusherActor("pusher_stdout", HWPCReport, mongodb, verbose=True)

    # Dispatcher
    dispatcher = DispatcherActor('dispatcher',
                                 lambda name, verbose:
                                 TestFormulaActor(name, pusher,
                                                  verbose=verbose),
                                 verbose=True)
    dispatcher.group_by(HWPCReport, HWPCGroupBy(HWPCDepthLevel.SOCKET,
                                                primary=True))

    # Puller
    csvdb = CsvDB(HWPCModel(), ['/home/jordan/git/smartwatts/data/core',
                                '/home/jordan/git/smartwatts/data/pcu',
                                '/home/jordan/git/smartwatts/data/rapl'])
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, dispatcher)
    puller = PullerActor("puller_mongo", csvdb,
                         hwpc_filter, 1000, verbose=True)

    pusher.start()
    dispatcher.start()
    puller.start()
    dispatcher.join()
    pusher.join()
    puller.kill()


main()
