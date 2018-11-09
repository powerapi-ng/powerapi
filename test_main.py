"""
smartwatts utilisation example
"""

import os
from smartwatts.pusher import ActorPusher
from smartwatts.database import StdoutDB, MongoDB
from smartwatts.formula import ActorTestFormula
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel, TestGroupBy
from smartwatts.filter import HWPCFilter
from smartwatts.puller import ActorPuller
from smartwatts.report import HWPCReport
from smartwatts.formula_dispatcher import ActorFormulaDispatcher


def log(msg):
    """ log """
    print('[' + str(os.getpid()) + '] ' + msg)


log('I\'m main')


def main():
    """ main """

    # Pusher
    stdoutdb = StdoutDB()
    pusher = ActorPusher("pusher_stdout", HWPCReport, stdoutdb, verbose=True)

    # Dispatcher
    dispatcher = ActorFormulaDispatcher('dispatcher',
                                        lambda name, verbose:
                                        ActorTestFormula(name, pusher,
                                                         verbose=verbose),
                                        verbose=True)
    dispatcher.group_by(HWPCReport, HWPCGroupBy(HWPCDepthLevel.CORE,
                                                primary=True))

    # Puller
    mongodb = MongoDB('localhost', 27017, 'smartwatts', 'sensor')
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, dispatcher)
    puller = ActorPuller("puller_mongo", mongodb,
                         hwpc_filter, 10, verbose=True)

    pusher.start()
    dispatcher.start()
    puller.start()
    dispatcher.join()
    pusher.join()
    puller.kill()


main()
