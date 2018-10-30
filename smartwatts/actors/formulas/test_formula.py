from smartwatts.actors.formulas.abstract_formula import AbstractFormula
import smartwatts.config as config

class TestFormulaFactory:

    def gen_formula(context, formula_id, reporter, data_arch, verbose):
        formula = _TestFormula(context, formula_id,
                               config.SOCKET_PATH+'/formula_'+formula_id,
                               reporter, data_arch, verbose)
        formula.start()
        return formula

class _TestFormula(AbstractFormula):
    def handle_message(self, msg):
        if ActorReceive.handle_message(self, msg):
            return True
        if msg.message_type == HWPC_REPORT:
            time.sleep(1)
            msg = EstimationMessage(42)
            self.reporter.send(msg)
            return True
        return False
