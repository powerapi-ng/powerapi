"""
Module test_actor_puller
"""

import zmq
from smartwatts.puller import ActorPuller
from smartwatts.database import MongoDB
from smartwatts.filter import HWPCFilter
from smartwatts.report import HWPCReport
from smartwatts.report_model import HWPCModel
from smartwatts.test import MessageInterceptor

#########################################
# Initialization functions
#########################################


def get_hwpc_mongodb(collection):
    """ Return a MongoDB object for hwpc report """
    return MongoDB(HWPCModel(), 'localhost', 27017, 'test_puller', collection)


def get_hwpc_filter(dispatch):
    """ Return hwpcfilter with rule for the param dispatch """
    hwpc_filter = HWPCFilter()
    hwpc_filter.filter(lambda msg: True, dispatch)
    return hwpc_filter

#########################################


class TestActorPuller:
    """ TestActorPuller class """

    def test_basic_db(self):
        """ Test get 10 simple HWPCReport """
        context = zmq.Context()
        interceptor = MessageInterceptor(context)
        puller = ActorPuller("puller_mongo", get_hwpc_mongodb('test_puller1'),
                             get_hwpc_filter(interceptor), 10)
        puller.start()
        puller.connect(context)

        # Get the 10 HWPCReport
        for _ in range(10):
            report = interceptor.receive(100)
            assert isinstance(report, HWPCReport)

        # Get one more
        report = interceptor.receive(100)
        assert report is None

        puller.kill()
