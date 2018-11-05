"""
Module class Router
"""
import zmq
from smartwatts.actor import Actor
from smartwatts.actor.basic_messages import UnknowMessageTypeException

class ActorFormulaDispatcher(Actor):
    """
    receive interface:
        report_data: route this message to the corresponding Formula Actor,
                     create a new one if no Formula exist to handle
                     this message
    """

    def __init__(self, name, reporter, formula_init_function, verbose=False):

        """
        Parameters:
            reporter(smartwatts.reporter.Reporter): reporter used to store
                                                    Formula reports in
                                                    databases
            formula_init_function(fun () -> smartwatts.formula.Formula):
        """
        Actor.__init__(self, name, verbose)

        # self.pull_socket_name = pull_socket_name
        self.reporter = reporter
        self.formulas = {}
        self.route_table = []
        self.formula_init_function = formula_init_function

    def init_actor(self):
        pass

    def terminated_behaviour(self):
        """
        kill each formula before terminate
        """
        for name, formula in self.formulas.items():
            self.log('kill ' + name)
            formula.kill()

    def initial_receive(self, msg):
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                for formula_id, report in group_by_rule(msg):
                    if formula_id not in self.formulas:
                        self.log('create formula ' + formula_id)
                        arch_data = self.__get_arch_data(report)
                        self.__create_formula(formula_id, arch_data)
                    self.formulas[formula_id].send(report)
                return
        raise UnknowMessageTypeException(type(msg))

    def __get_arch_data(self, msg):
        """
        return architecture informations that correpond to the given report
        """
        return 0
    def __create_formula(self, formula_id, arch_data):
        """
        create formula from router
        """
        formula = self.formula_init_function(formula_id, self.reporter,
                                             arch_data, self.verbose)
        self.formulas[formula_id] = formula
        formula.connect(self.context)

    def group_by(self, report_class, group_by_rule, primary=False):
        self.route_table.append((report_class, group_by_rule))
