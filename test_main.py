from smartwatts.reporter import ActorReporter
from smartwatts.database import Stdout, Stdin
from smartwatts.formula import ActorTestFormula
from smartwatts.group_by import test_group_by, hwpc_group_by, HWPCDepthLevel
from smartwatts.filter import TestFilter
from smartwatts.report import *
from smartwatts.puller import ActorPuller
from smartwatts.formula_dispatcher import ActorFormulaDispatcher

def log(msg):
    print('['+str(os.getpid())+'] '+msg)
log('i\'m main')

out1 = Stdout()
reporter = ActorReporter()
reporter.store(TestReport, out1)
reporter.store(PowerReport, out1)

fd = ActorFormulaDispatcher(reporter, lambda name, reporter, arch_data, verbose:
                            ActorTestFormula(name, reporter, arch_data,
                                             verbose=verbose))
fd.group_by(TestReport, test_group_by())
fd.group_by(HWPCReport, hwpc_group_by(HWPCDepthLevel.CORE), primary=True)

in1 = Stdin()
test_filter = TestFilter()
test_filter.filter(lambda r: fd)

puller = ActorPuller(in1, test_filter)

fd.start()
puller.start()
fd.join()
puller.kill()
