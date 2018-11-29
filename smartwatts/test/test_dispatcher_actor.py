import pytest

from smartwatts.dispatcher import FormulaDispatcherReportHandler
from smartwatts.message import UnknowMessageTypeException
from smartwatts.group_by import AbstractGroupBy
from smartwatts.report import Report

class Report1(Report):
    """ Fake report that can contain 2 or three values *a*, *b*, and *b2* """
    def __init__(self, a, b, b2=None):
        self.a = a
        self.b = b
        self.b2 = b2

    def __eq__(self, other):
        if not isinstance(other, Report1):
            return False
        return other.a == self.a and other.b == self.b and other.b2 == self.b2


class GroupBy1A(AbstractGroupBy):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A']

    def extract(self, report):
        return [((report.a,), report)]


class GroupBy1AB(AbstractGroupBy):
    """Group by rule that split the report if it contains a *b2* value

    if the report contain a *b2* value, it is spliten in two report the first
    one containing the *b* value and the second one containing the *b2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *b* value or the *b2 value of the
    report

    """
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A', 'B']

    def extract(self, report):
        b2_report = [] if report.b2 is None else [
            ((report.a, report.b2), Report1(report.a, report.b2))
        ]
        return [((report.a, report.b), Report1(report.a, report.b))] + b2_report


class Report2(Report):
    """ Fake report that can contains two or three values : *a*, *c*, *c2* """
    def __init__(self, a, c, c2=None):
        self.a = a
        self.c = c
        self.c2 = c2

    def __eq__(self, other):
        if not isinstance(other, Report2):
            return False
        return other.a == self.a and other.c == self.c and other.c2 == self.c2


class GroupBy2A(AbstractGroupBy):
    """ Group by rule that return the received report

    its id is the report *a* value

    """
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A']

    def extract(self, report):
        return [((report.a,), report)]


class GroupBy2AC(AbstractGroupBy):
    """Group by rule that split the report if it contains a *c2* value

    if the report contain a *c2* value, it is spliten in two report the first
    one containing the *c* value and the second one containing the *c2* value

    sub-report identifier is a tuple of two values, the first one is the *a*
    value of the report, the second one is the *c* value or the *c2 value of the
    report

    """
    def __init__(self, primary=False):
        AbstractGroupBy.__init__(self, primary)
        self.fields = ['A', 'C']

    def extract(self, report):
        c2_report = [] if report.c2 is None else [
            ((report.a, report.c2), Report2(report.a, report.c2))
        ]
        return [((report.a, report.c), Report2(report.a, report.c))] + c2_report


# Inputs reports
REPORT_1 = Report1('a', 'b')
REPORT_1_B2 = Report1('a', 'b', 'b2')
REPORT_2 = Report2('a', 'c')
REPORT_2_C2 = Report2('a', 'c', 'c2')

# Report that could be return by the handle function
SPLITED_REPORT_1_B2 = Report1('a', 'b2')
SPLITED_REPORT_2_C2 = Report2('a', 'c2')


class TestHandleFunction:
    """Test handle function of the formula dispatcher handler

        The first test case test empty route table rule

        The other function test name describe the initial test of the handler
        before to use its handle function. It is writen like this :
        test_handle_pgb_PRIMARY_GROUPBY_RULE_CLASSE_gb_OTHER_GROUPBY_RULE_CLASS

        For each of theses functions, we test the result of handle function on 4
        predefinded reports defined below as constants.

    """

    def gen_handle_test(self, route_table, primary_group_by_rule, input_report,
                        validation_reports):
        """instanciate the handler whit given route table and primary groupby
        rule, test if the handle function application on *input_report* return
        the same reports as in *validation_reports*

        """
        handler = FormulaDispatcherReportHandler(route_table,
                                                 primary_group_by_rule)
        result = handler.handle(input_report)

        result.sort(key=lambda result_tuple: result_tuple[0])
        validation_reports.sort(key=lambda result_tuple: result_tuple[0])

        assert result == validation_reports

    def test_empty_no_associated_group_by_rule(self):
        """
        Test if an UnknowMessageTypeException is raised when using handle
        function on a report that is not associated with a group_by rule in the
        handler's route table

        """
        handler = FormulaDispatcherReportHandler([], GroupBy1A())

        with pytest.raises(UnknowMessageTypeException):
            handler.handle(REPORT_1)

    def test_handle_pgb_GroupBy1A_gb_GroupBy2A(self):
        """
        Test the handler with a GroupBy1A rule for Report1 as primary rule and
        GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a',), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a',), REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2_C2)]

        """
        route_table = [(Report1, GroupBy1A()), (Report2, GroupBy2A())]

        self.gen_handle_test(route_table, GroupBy1A(), REPORT_1,
                             [(('a',), REPORT_1)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_2,
                             [(('a',), REPORT_2)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_1_B2,
                             [(('a',), REPORT_1_B2)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_2_C2,
                             [(('a',), REPORT_2_C2)])

    def test_handle_pgb_GroupBy1A_gb_GroupBy2AC(self):
        """
        Test the handler with a GroupBy1A rule for Report1 as primary rule and
        GroupBy2AC rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a',), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a',), REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2),
                         (('a',), SPLITED_REPORT_2_C2)]

        """
        route_table = [(Report1, GroupBy1A()), (Report2, GroupBy2AC())]

        self.gen_handle_test(route_table, GroupBy1A(), REPORT_1,
                             [(('a',), REPORT_1)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_2,
                             [(('a',), REPORT_2)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_1_B2,
                             [(('a',), REPORT_1_B2)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_2_C2,
                             [(('a',), REPORT_2),
                              (('a',), SPLITED_REPORT_2_C2)])

    def test_handle_pgb_GroupBy1AB_gb_GroupBy2A(self):
        """
        Test the handler with a GroupBy1AB rule for Report1 as primary rule and
        GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a', 'b'), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a', 'b'), REPORT_1_B2),
                         (('a', 'b2'), SPLITED_REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2_C2)]

        """
        route_table = [(Report1, GroupBy1AB()), (Report2, GroupBy2A())]

        print(GroupBy2A().extract(REPORT_2))
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_1,
                             [(('a', 'b'), REPORT_1)])
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_2,
                             [(('a',), REPORT_2)])
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_1_B2,
                             [(('a', 'b'), REPORT_1),
                              (('a', 'b2'), SPLITED_REPORT_1_B2)])
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_2_C2,
                             [(('a',), REPORT_2_C2)])

    def test_handle_pgb_GroupBy1AB_gb_GroupBy2AC(self):
        """
        Test the handler with a GroupBy1AB rule for Report1 as primary rule and
        GroupBy2A rule for Report2

        Expected result for each input report :
        - REPORT_1 : [(('a', 'b'), REPORT_1)]
        - REPORT_2 : [(('a',), REPORT_2)]
        - REPORT_1_B2 : [(('a', 'b'), REPORT_1_B2),
                         (('a', 'b2'), SPLITED_REPORT_1_B2)]
        - REPORT_2_C2 : [(('a',), REPORT_2),
                         (('a',), SPLITED_REPORT_2_C2)]
        """
        route_table = [(Report1, GroupBy1AB()), (Report2, GroupBy2AC())]

        print(GroupBy2A().extract(REPORT_2))
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_1,
                             [(('a', 'b'), REPORT_1)])
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_2,
                             [(('a',), REPORT_2)])
        self.gen_handle_test(route_table, GroupBy1AB(), REPORT_1_B2,
                             [(('a', 'b'), REPORT_1),
                              (('a', 'b2'), SPLITED_REPORT_1_B2)])
        self.gen_handle_test(route_table, GroupBy1A(), REPORT_2_C2,
                             [(('a',), REPORT_2),
                              (('a',), SPLITED_REPORT_2_C2)])
