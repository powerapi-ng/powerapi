"""
Module class Formula
"""

import time
from smartwatts.actors.abstract import ActorReceive
import smartwatts.config as config
from smartwatts.message import EstimationMessage


def gen_formula(context, formula_id, reporter, data_arch, verbose):
    """ Factory function for generate Formula """
    formula = Formula(context, formula_id,
                      config.SOCKET_PATH+'/formula_'+formula_id,
                      reporter, data_arch, verbose)
    formula.start()
    return formula


class AbstractFormula(ActorReceive):

    """
    receive interface:
        data_msg : sleep for 1s and send 42 to the reporter
    """

    def __init__(self, context, name, socket_address, reporter, data_arch,
                 verbose=False):
        """
        params:
            data arch(???) : data of the monitored architecture
        """
        ActorReceive.__init__(self, context, name, socket_address, verbose)
        self.reporter = reporter
        self.data_arch = data_arch

    def init_actor(self):
        """
        connect to the reporter actor
        """
        self.reporter.connect()

    def handle_message(self, msg):
        if ActorReceive.handle_message(self, msg):
            return True
        if msg.message_type == HWPC_REPORT:
            time.sleep(1)
            msg = EstimationMessage(42)
            self.reporter.send(msg)
            return True
        return False
