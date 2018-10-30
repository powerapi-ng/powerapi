"""
Module class Router
"""
import zmq
import smartwatts.config as config
from smartwatts.actors.abstract import PullActor
from smartwatts.message import *


class FormulaTypeNotFoundException(Exception):
    pass

def gen_router(context, reporter, route_table, formula_type_table,
               verbose=False):
    """
    Parameters:
        context(zmq.Context):context of the processus that create the actor
        cmd_socket_address(str) :
        pull_checker_address(str) : address of the socket used for communication
                                    between the db_checker actor and the router
        route_table (dict(message._Message_type : (message.Message)->
                     [(formula_id(tuple), message.Message)] : table that contain
                     route rules (mapping from message  type to groupBy function
        formula_type_table([(re.Pattern, actors.formulas.AbstractFormula)]):
                           table that contain mapping from sensor name matching
                           rules to the sensor corresponding formula factory
    """
    router = Router(context, 'router', config.ROUTER_SOCKET_ADDRESS,
                    config.ROUTER_PUSH_SOCKET_ADDRESS, reporter, route_table,
                    formula_type_table, verbose)
    router.start()
    router.connect()
    return router

class Router(PullActor):
    """
    receive interface:
        report_data: route this message to the corresponding Formula Actor,
                     create a new one if no Formula exist to handle
                     this message
    """

    def __init__(self, context, name, cmd_socket_address, pull_socket_address,
                 reporter, route_table = {}, formula_type_table = [],
                 verbose=False):

        """
        Parameters: (see gen_router)
        """
        PullActor.__init__(self, context, name, cmd_socket_address,
                           pull_socket_address, verbose=verbose)

        # self.pull_socket_name = pull_socket_name
        self.reporter = reporter
        self.formulas = {}
        self.route_table = route_table
        self.formula_type_table = formula_type_table

    def get_data_arch(self, msg):
        """
        return architecture informations that correpond to the given report
        """
        return 0

    def create_formula(self, sensor_name, formula_id, data_arch):
        """
        Allow to create formula from router
        """
        i = 0
        pattern_found = False
        while (not pattern_found) or (i <= len(self.formula_type_table)):
            sensor_name_pattern, formula_factory = self.formula_type_table[i]
            if sensor_name_pattern.fullmatch(sensor_name) != None:
                formula = formula_factory.gen_formula(self.context, formula_id,
                                                      self.reporter, data_arch,
                                                      self.verbose)
                self.formulas[formula_id] = formula
                pattern_found = True

        if not pattern_found:
            raise NoFormulaTypeFoundException('sensor name : ' + sensor_name)

    def terminated_behaviour(self):
        """
        kill each formula before terminate
        """
        PullActor.terminated_behaviour(self)
        for name, formula in self.formulas.items():
            self.log('kill ' + name)
            formula.kill()

    def handle_report(self, msg, groupBy_rule):
        for formula_id, report_message in groupBy_rule(msg):
        # if the corresponding formula doesn't exist, create it
            if formula_id not in self.formulas:
                self.log('create formula ' + formula_id)
                data_arch = self.get_data_arch(msg)
                self.create_formula(formula_id, data_arch)
            # route the message to the corresponding formula
            self.formulas[formula_id].send_cmd_msg(report_message)

    def handle_message(self, msg):
        if PullActor.handle_message(self, msg):
            return True
        if msg.message_type in self.route_table:
            self.handle_report(msg, self.route_table[msg.message_type])
            return True
        else:
            return False
