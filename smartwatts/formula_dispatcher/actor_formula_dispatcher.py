"""
Module class Router
"""
from smartwatts.actor import Actor
from smartwatts.actor.basic_messages import UnknowMessageTypeException
from smartwatts.utils.tree import Tree


class NoPrimaryGroupByRuleException(Exception):
    """
    Exception launched when user want to get the primary group_by rule on a
    formula dispatcher that doesn't have one
    """
    pass


class PrimaryGroupByRuleAlreadyDefinedException(Exception):
    """
    Exception launched when user want to add a primary group_by rule on a
    formula dispatcher that already have one
    """
    pass


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
        self.formula_dict = {}
        self.formula_tree = Tree()
        self.route_table = []
        self.formula_init_function = formula_init_function
        self.primary_group_by_rule = None

    def init_actor(self):
        pass

    def terminated_behaviour(self):
        """
        kill each formula before terminate
        """
        for name, formula in self.formula_dict.items():
            self.log('kill ' + name)
            formula.kill()

    def initial_receive(self, msg):
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                for formula_id, report in self._extract_reports(msg,
                                                                group_by_rule):
                    self._send_to_formula(report, formula_id)
                return
        raise UnknowMessageTypeException(type(msg))

    def _extract_reports(self, report, group_by_rule):
        """
        use the group by rule to split the report. Generated report identifier
        are then mapped to an identifier that match the primary report
        identifier fields
        """
        # list of tuple (id_report, report)
        report_list = group_by_rule.extract(report)

        if group_by_rule.is_primary:
            return report_list

        return list(map(lambda tuple:
                        (self._match_report_id(tuple[0], group_by_rule),
                         tuple[1]),
                        report_list))

    def _match_report_id(self, report_id, group_by_rule):
        new_report_id = ()
        primary_rule = self._get_primary_group_by_rule()
        for i in range(len(report_id)):
            if group_by_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id

    def _get_primary_group_by_rule(self):
        if self.primary_group_by_rule is not None:
            return self.primary_group_by_rule
        raise NoPrimaryGroupByRuleException

    def _send_to_formula(self, report, formula_id):
        """send the report to all the formula that match the formula_id

        if the formula id identify an unique formula and the formula doesn't
        exist, create it
        """
        if len(formula_id) == len(self.primary_group_by_rule):
            if formula_id not in self.formula_dict:
                self._create_formula(formula_id)
            self.formula_dict[formula_id].send(report)
        else:
            for formula in self.formula_tree.get(list(formula_id)):
                formula.send(report)

    def _create_formula(self, formula_id):
        """
        create formula from router
        """
        formula = self.formula_init_function(formula_id, self.reporter,
                                             self.verbose)

        formula.connect(self.context)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)

    def group_by(self, report_class, group_by_rule):
        """Add a group_by rule to the formula dispatcher

        Parameters:
            report_class(type): type of the message that the groub_by rule must
                                handle
            group_by_rule(group_by.AbstractGroupBy): group_by rule to add
        """
        if group_by_rule.is_primary:
            if self.primary_group_by_rule is not None:
                raise PrimaryGroupByRuleAlreadyDefinedException
            self.primary_group_by_rule = group_by_rule

        self.route_table.append((report_class, group_by_rule))
