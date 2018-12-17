"""
Handlers used by PusherActor
"""
from smartwatts.handler import AbstractInitHandler, AbstractHandler
from smartwatts.report import PowerReport
from smartwatts.message import UnknowMessageTypeException, ErrorMessage
from smartwatts.message import OKMessage
from smartwatts.database import DBErrorException


class StartHandler(AbstractHandler):
    """ Handle Start Message """

    def handle(self, msg, state):
        """ Initialize the output database
        """

        if state.initialized:
            return state

        try:
            state.database.load()
        except DBErrorException as error:
            state.socket_interface.send_monitor(ErrorMessage(error.msg))
            return state

        state.initialized = True
        state.socket_interface.send_monitor(OKMessage())
        return state


class PowerHandler(AbstractInitHandler):
    """
    HWPCHandler class
    """

    def handle(self, msg, state):
        """
        Override

        Save the msg in the database
        """
        if not isinstance(msg, PowerReport):
            raise UnknowMessageTypeException

        state.database.save(msg.serialize())
        return state
