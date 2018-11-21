"""
Module class Router
"""

from smartwatts.actor import Actor
from smartwatts.message import UnknowMessageTypeException
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
    ActorFormulaDispatcher class.

    receive interface:
        report_data: route this message to the corresponding Formula Actor,
                     create a new one if no Formula exist to handle
                     this message
    """

    def __init__(self, name, formula_init_function, verbose=False):
        """
        Parameters:
            @formula_init_function(fun () -> smartwatts.formula.Formula):
                Formula Factory.
        """
        Actor.__init__(self, name, verbose)

        # Formula containers
        self.formula_dict = {}
        self.formula_tree = Tree()

        # Array of tuple (report_class, group_by_rule)
        self.route_table = []

        # Formula factory
        self.formula_init_function = formula_init_function

        # Primary XXXGroupBy
        self.primary_group_by_rule = None

    def init_actor(self):
        """ Override """
        pass

    def terminated_behaviour(self):
        """
        Kill each formula before terminate
        """
        for name, formula in self.formula_dict.items():
            self.log('kill ' + name)
            formula.kill()

    def initial_receive(self, msg):
        """
        Override

        Loop since we find a route for this type of message
        Else it raise an error
        """

        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                for formula_id, report in self._extract_reports(msg,
                                                                group_by_rule):
                    self._send_to_formula(report, formula_id)
                return
        raise UnknowMessageTypeException(type(msg))

    def _extract_reports(self, report, group_by_rule):
        """
        Use the group by rule to split the report. Generated report identifier
        are then mapped to an identifier that match the primary report
        identifier fields

        ex: primary group_by (sensor, socket, core)
            second  group_by (sensor)
        The second group_by need to match with the primary if sensor are equal.

        Parameters:
            @report:        XXXReport instance
            @group_by_rule: XXXGroupBy instance
        """

        # List of tuple (id_report, report)
        report_list = group_by_rule.extract(report)

        if group_by_rule.is_primary:
            return report_list

        return list(map(lambda _tuple:
                        (self._match_report_id(_tuple[0], group_by_rule),
                         _tuple[1]),
                        report_list))

    def _match_report_id(self, report_id, group_by_rule):
        """
        Return the new_report_id with the report_id by removing
        every "useless" fields from it.

        Parameters:
            @report_id:     tuple of fields (id)
            @group_by_rule: XXXGroupBy instance
        """
        new_report_id = ()
        primary_rule = self._get_primary_group_by_rule()
        for i in range(len(report_id)):
            if group_by_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id

    def _get_primary_group_by_rule(self):
        """
        Return the primary group_by rule
        """
        if self.primary_group_by_rule is not None:
            return self.primary_group_by_rule
        raise NoPrimaryGroupByRuleException

    def _send_to_formula(self, report, formula_id):
        """
        Send the report to all the formula that match the formula_id

        if the formula id identify an unique formula and the formula doesn't
        exist, create it
        """
        if len(formula_id) == len(self.primary_group_by_rule.fields):
            if formula_id not in self.formula_dict:
                self._create_formula(formula_id)
            self.formula_dict[formula_id].send(report)
        else:
            for formula in self.formula_tree.get(list(formula_id)):
                formula.send(report)

    def _create_formula(self, formula_id):
        """
        Create formula from router
        """
        formula = self.formula_init_function(str(formula_id), self.verbose)

        formula.connect(self.context)
        self.formula_dict[formula_id] = formula
        self.formula_tree.add(list(formula_id), formula)
        self.formula_dict[formula_id].start()

    def group_by(self, report_class, group_by_rule):
        """
        Add a group_by rule to the formula dispatcher

        Parameters:
            @report_class(type): type of the message that the
                                 groub_by rule must handle
            @group_by_rule(group_by.AbstractGroupBy): group_by rule to add
        """
        if group_by_rule.is_primary:
            if self.primary_group_by_rule is not None:
                raise PrimaryGroupByRuleAlreadyDefinedException
            self.primary_group_by_rule = group_by_rule

        self.route_table.append((report_class, group_by_rule))

    def behaviour(self):
        """ Override """
        pass
