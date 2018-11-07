"""
smartwatts utilisation example
"""

import os
from smartwatts.reporter import ActorReporter
from smartwatts.database import Stdout, Stdin
from smartwatts.formula import ActorTestFormula
from smartwatts.group_by import HWPCGroupBy, HWPCDepthLevel, TestGroupBy
from smartwatts.filter import TestFilter
from smartwatts.report import TestReport, HWPCReport, PowerReport
from smartwatts.puller import ActorPuller
from smartwatts.formula_dispatcher import ActorFormulaDispatcher


def log(msg):
    print('[' + str(os.getpid()) + '] ' + msg)


log('i\'m main')


def main():
    out1 = Stdout()
    reporter = ActorReporter()
    reporter.store(TestReport, out1)
    reporter.store(PowerReport, out1)

    dispatcher = ActorFormulaDispatcher(reporter, lambda name, reporter,
                                        arch_data, verbose:
                                        ActorTestFormula(name, reporter,
                                                         arch_data,
                                                         verbose=verbose))
    dispatcher.group_by(TestReport, TestGroupBy())
    dispatcher.group_by(HWPCReport, HWPCGroupBy(HWPCDepthLevel.CORE,
                                                primary=True))

    in1 = Stdin()
    test_filter = TestFilter()
    test_filter.filter(lambda r: dispatcher)

    puller = ActorPuller(in1, test_filter)

    dispatcher.start()
    puller.start()
    dispatcher.join()
    puller.kill()

main()
