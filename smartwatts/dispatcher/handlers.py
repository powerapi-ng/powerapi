"""
Handlers used by the DispatcherActor
"""
from smartwatts.handler import AbstractInitHandler, AbstractHandler
from smartwatts.message import UnknowMessageTypeException
from smartwatts.message import OKMessage, StartMessage


class StartHandler(AbstractHandler):
    """ Initialize the receved state
    """
    def handle(self, msg, state):
        if state.initialized:
            return state

        if not isinstance(msg, StartMessage):
            return state

        state.initialized = True
        state.socket_interface.send_monitor(OKMessage())

        return state


class FormulaDispatcherReportHandler(AbstractInitHandler):
    """
    Split the received report into sub-reports (if needed) and return the sub
    reports and formulas ids to send theses report
    """

    def __init__(self, route_table, primary_group_by_rule):
        """
        Parameters:
            @route_table([(Message, AbstractGroupBy)]: list all group by rule
                                                       with their associated
                                                       message type

        """
        # Array of tuple (report_class, group_by_rule)
        self.route_table = route_table

        # Primary GroupBy
        self.primary_group_by_rule = primary_group_by_rule

    def handle(self, msg, state):
        """
        Split the received report into sub-reports (if needed) and send them to
        their corresponding formula

        if the corresponfing formula does not exist, create and return the
        actor state, containing the new formula

        Parameters:
            msg(smartwatts.report.Report)

        Return:
            [(tuple, smartwatts.report.Report)]: list of *(formula_id, report)*.
                                                 The formula_id is a tuple that
                                                 identify the formula_actor
        """
        for (report_class, group_by_rule) in self.route_table:
            if isinstance(msg, report_class):
                for formula_id, report in self._extract_reports(msg,
                                                                group_by_rule):
                    primary_rule_fields = self.primary_group_by_rule.fields
                    if len(formula_id) == len(primary_rule_fields):
                        formula = state.get_direct_formula(formula_id)
                        if formula is None:
                            state.add_formula(formula_id)
                        else:
                            formula.send(report)
                    else:
                        for formula in state.get_corresponding_formula(
                                list(formula_id)):
                            formula.send(report)

                return state

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

        Return:
            ([(tuple, Report]): list of (formula_id, Report)
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
        primary_rule = self.primary_group_by_rule
        for i in range(len(report_id)):
            if i >= len(primary_rule.fields):
                return new_report_id
            if group_by_rule.fields[i] == primary_rule.fields[i]:
                new_report_id += (report_id[i],)
            else:
                return new_report_id
        return new_report_id
