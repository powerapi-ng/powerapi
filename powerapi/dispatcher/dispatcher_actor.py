# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from typing import Type, Tuple, List

from thespian.actors import ActorAddress, ActorExitRequest, ChildActorExited, PoisonMessage

from powerapi.actor import Actor, InitializationException
from powerapi.formula import FormulaActor, FormulaValues
from powerapi.dispatch_rule import DispatchRule
from powerapi.utils import Tree
from powerapi.report import Report
from powerapi.message import StartMessage, DispatcherStartMessage, FormulaStartMessage, EndMessage, ErrorMessage, OKMessage
from powerapi.dispatcher.blocking_detector import BlockingDetector
from powerapi.dispatcher.route_table import RouteTable


def _clean_list(id_list):
    """
    return a list where all elements are unique
    """
    id_list.sort()
    r_list = []
    last_element = None
    for x in id_list:
        if x != last_element:
            r_list.append(x)
            last_element = x
    return r_list


def _extract_formula_id(report: Report, dispatch_rule: DispatchRule, primary_dispatch_rule: DispatchRule) -> List[Tuple]:
    """
    Use the dispatcha rule to extract formula_id from the given report.
    Formula id are then mapped to an identifier that match the primary
    report identifier fields

    ex: primary dispatch_rule (sensor, socket, core)
        second  dispatch_rule (sensor)
    The second dispatch_rule need to match with the primary if sensor are
    equal.

    :param powerapi.Report report:                 Report to split
    :param powerapi.DispatchRule dispatch_rule: DispatchRule rule

    :return: List of formula_id associated to a sub-report of report
    :rtype: [tuple]
    """

    # List of tuple (id_report, report)
    id_list = dispatch_rule.get_formula_id(report)
    if dispatch_rule.is_primary:
        return id_list

    def f(formula_id):
        return _match_report_id(formula_id, dispatch_rule, primary_dispatch_rule)

    return _clean_list(list(map(f, id_list)))


def _match_report_id(report_id: Tuple, dispatch_rule: DispatchRule, primary_rule: DispatchRule) -> Tuple:
    """
    Return the new_report_id with the report_id by removing
    every "useless" fields from it.

    :param tuple report_id:                     Original report id
    :param powerapi.DispatchRule dispatch_rule: DispatchRule rule
    """
    new_report_id = ()
    for i in range(len(report_id)):
        if i >= len(primary_rule.fields):
            return new_report_id
        if dispatch_rule.fields[i] == primary_rule.fields[i]:
            new_report_id += (report_id[i], )
        else:
            return new_report_id
    return new_report_id


class DispatcherActor(Actor):
    """
    DispatcherActor class herited from Actor.

    Route message to the corresponding Formula, and create new one
    if no Formula exist for this message.
    """

    def __init__(self):
        Actor.__init__(self, DispatcherStartMessage)

        self.formula_class: Type[FormulaActor] = None
        self.formula_values: FormulaValues = None
        self.route_table: RouteTable = None
        self.device_id = None

        self._exit_mode = False
        self.formula_name_service = None
        self.formula_waiting_service = FormulaWaitingService()
        self.formula_pool = {}
        self.formula_number_id = 0

    def _initialization(self, message: StartMessage):
        Actor._initialization(self, message)
        self.formula_class = message.formula_class
        self.formula_values = message.formula_values
        self.route_table = message.route_table
        self.device_id = message.device_id

        self.formula_name_service = FormulaNameService()

        if self.route_table.primary_dispatch_rule is None:
            raise InitializationException('Dispatcher initialized without primary dispatch rule')

    def receiveMsg_PoisonMessage(self, message: PoisonMessage, sender: ActorAddress):
        """
        When receiving a PoisonMessage from a formula :
            - notify the formula blocking detector that a formula send a PoisonMessage
            - check from the blocking detector if the formula crashed
            - if the formula crashed, restart it
        """
        poison_message = message.poisonMessage
        for formula_name, (formula, blocking_detector) in self.formula_pool.items():
            if sender == formula:
                log_line = 'received poison messsage from formula ' + formula_name + ' for message ' + str(poison_message)
                log_line += 'with this error stack : ' + message.details
                self.log_debug(log_line)
                blocking_detector.notify_poison_received(poison_message)
                if blocking_detector.is_blocked():
                    self.log_debug('formula ' + formula_name + ' is blocked : ' + str(blocking_detector.is_blocked()))
                    self.log_debug('restart formula ' + formula_name)
                    self.log_error('formula ' + formula_name + ' is blocked after this error : ' + message.details)
                    self._restart_formula(formula_name)
                    return

    def receiveMsg_ActorExitRequest(self, message: ActorExitRequest, sender: ActorAddress):
        """
        When receiving ActorExitRequest, forward it to all formula
        """
        Actor.receiveMsg_ActorExitRequest(self, message, sender)
        for _, (formula, __) in self.formula_pool.items():
            self.send(formula, ActorExitRequest())
        for _, formula in self.formula_waiting_service.get_all_formula():
            self.send(formula, ActorExitRequest())

    def _gen_formula_name(self, formula_id):
        name = 'formula' + str(self.formula_number_id)
        self.formula_number_id += 1
        for field in formula_id:
            name += '__' + str(field)
        return name

    def _send_message(self, formula_name, message):
        try:
            formula, blocking_detector = self.formula_pool[formula_name]
            message.dispatcher_report_id = blocking_detector.get_message_id()
            self.log_debug('send ' + str(message) + ' to ' + formula_name)
            self.send(formula, message)
        except KeyError:
            self.formula_waiting_service.add_message(formula_name, message)

    def receiveMsg_Report(self, message: Report, _: ActorAddress):
        """
        When receiving a report, split it into sub-reports (if needed) and send them to their corresponding formula.
        If the corresponding formula does not exist, the dispatcher create it and send it the report
        """
        self.log_debug('received ' + str(message))
        dispatch_rule = self.route_table.get_dispatch_rule(message)
        primary_dispatch_rule = self.route_table.primary_dispatch_rule
        if dispatch_rule is None:
            self.log_warning('no dispatch rule for report ' + str(message))
            return
        formula_ids = _extract_formula_id(message, dispatch_rule, primary_dispatch_rule)

        for formula_id in formula_ids:
            primary_rule_fields = primary_dispatch_rule.fields
            if len(formula_id) == len(primary_rule_fields):
                try:
                    formula_name = self.formula_name_service.get_direct_formula_name(formula_id)
                    self._send_message(formula_name, message)
                except KeyError:
                    formula_name = self._gen_formula_name(formula_id)
                    self.log_info('create formula ' + formula_name)
                    formula = self._create_formula(formula_id, formula_name)
                    self.formula_name_service.add(formula_id, formula_name)
                    self.formula_waiting_service.add(formula_name, formula)
                    self.formula_waiting_service.add_message(formula_name, message)
            else:
                for formula_name in self.formula_name_service.get_corresponding_formula(list(formula_id)):
                    self._send_message(formula_name, message)

    def _get_formula_name_from_address(self, formula_address: ActorAddress):
        for name, (address, _) in self.formula_pool.items():
            if formula_address == address:
                return name
        return self.formula_waiting_service.get_formula_by_address(formula_address)

    def receiveMsg_ChildActorExited(self, message: ChildActorExited, _: ActorAddress):
        """
        When receive ChildActorExited from a formula:
        remove formula from formula pool and if dispatcher is in exit_mode and no formula is running, send an EndMessage to all pusher
        """
        try:
            formula_name = self._get_formula_name_from_address(message.childAddress)
        except AttributeError:
            return
        self.formula_name_service.remove_formula(formula_name)
        del self.formula_pool[formula_name]
        if self._exit_mode and not self.formula_pool:
            for _, pusher in self.formula_values.pushers.items():
                self.send(pusher, EndMessage(self.name))
            self.send(self.myAddress, ActorExitRequest())

    def receiveMsg_ErrorMessage(self, message: ErrorMessage, _: ActorAddress):
        """
        When receiving an ErrorMessage after trying to start a formula, remove formula from waiting service
        """
        self.log_info('error while trying to start ' + message.sender_name + ' : ' + message.error_message)
        self.formula_waiting_service.remove_formula(message.sender_name)

    def receiveMsg_OKMessage(self, message: OKMessage, sender: ActorAddress):
        """
        When receiving OKMessage after trying to start a formula, move formula from the waiting service to the formula pool
        """
        formula_name = message.sender_name
        waiting_messages = self.formula_waiting_service.get_waiting_messages(formula_name)
        self.formula_waiting_service.remove_formula(formula_name)
        self.formula_pool[formula_name] = (sender, BlockingDetector())
        for waiting_msg in waiting_messages:
            self._send_message(formula_name, waiting_msg)
        self.log_info('formula ' + formula_name + 'started')

    def receiveMsg_EndMessage(self, message: EndMessage, _: ActorAddress):
        """
        When receiving an EndMessage, set dispatcher into exit_mode and send an EndMessage to all formula
        """
        self.log_debug('received message ' + str(message))
        self._exit_mode = True
        for _, (formula, __) in self.formula_pool.items():
            self.send(formula, EndMessage(self.name))
        for formula_name, _ in self.formula_waiting_service.get_all_formula():
            self.formula_waiting_service.add_message(formula_name, message)

    def _restart_formula(self, formula_name: str):
        formula, _ = self.formula_pool[formula_name]
        formula_id = self.formula_name_service.get_formula_id(formula_name)

        # remove crashed formula
        self.formula_name_service.remove_formula(formula_name)
        del self.formula_pool[formula_name]
        self.send(formula, ActorExitRequest())

        # create new formula
        new_name = self._gen_formula_name(formula_id)

        formula = self._create_formula(formula_id, new_name)
        self.formula_name_service.add(formula_id, new_name)
        self.formula_waiting_service.add(new_name, formula)
        self.log_debug('restart formula' + formula_name + ' with new name : ' + new_name)

    def _create_formula(self, formula_id: Tuple, formula_name: str) -> ActorAddress:
        formula = self.createActor(self.formula_class)
        domain_values = self.formula_class.gen_domain_values(self.device_id, formula_id)
        start_message = FormulaStartMessage(self.name, formula_name, self.formula_values, domain_values)
        self.send(formula, start_message)
        return formula


class FormulaWaitingService:
    """
    Pool of fomula that received a StartMessage but didn't answer yet
    """
    def __init__(self):
        self.formulas = {}
        self.waiting_messages = {}

    def get_all_formula(self) -> List[Tuple[str, ActorAddress]]:
        """
        :return: list of tuple (formula_name, formula_address)
        """
        return self.formulas.items()

    def add(self, formula_name: str, formula_address: ActorAddress):
        """
        add a formula to the waiting service
        """
        self.formulas[formula_name] = formula_address
        self.waiting_messages[formula_name] = []

    def add_message(self, formula_name: str, message: Report):
        """
        store a message receive by a not started formula
        """
        self.waiting_messages[formula_name].append(message)

    def get_waiting_messages(self, formula_name: str) -> List[Report]:
        """
        :return: the list of message receive by the formula since the first StartMessage was send to the formula
        :raise AttributeError: if no formula with the given name exists
        """
        if formula_name in self.formulas:
            return self.waiting_messages[formula_name]
        raise AttributeError('unknow formula ' + str(formula_name))

    def get_formula_by_address(self, formula_address: ActorAddress) -> str:
        """
        :return: the formula name bind to the given formula address
        :raise AttributeError: if no formula with the given address exists
        """
        for name, address in self.formulas.items():
            if formula_address == address:
                return name
        raise AttributeError('no such formula with address ' + str(formula_address))

    def remove_formula(self, formula_name: str):
        """
        remove formula from the waiting service
        :raise AttributeError: if no formula with the given name exists
        """
        if formula_name in self.formulas:
            del self.formulas[formula_name]
            del self.waiting_messages[formula_name]
        else:
            raise AttributeError('unknow formula ' + str(formula_name))


class FormulaNameService:
    """
    Service that make correspondance between formula name and formula id
    """
    def __init__(self):
        self.formula_name = {}
        self.formula_tree = Tree()

    def add(self, formula_id, formula_name: str):
        """
        add a formula name into the service with its main id
        """
        self.formula_name[formula_id] = formula_name
        self.formula_tree.add(list(formula_id), formula_name)

    def get_direct_formula_name(self, formula_id) -> str:
        """
        Get the formula corresponding to the given formula id
        or create and return it if its didn't exist

        :param tuple formula_id: Key corresponding to a Formula
        :return: a Formula name
        """

        return self.formula_name[formula_id]

    def get_formula_id(self, formula_name_to_find: str) -> Tuple:
        """
        return main formula id from formula name
        """
        for formula_id, formula_name in self.formula_name.items():
            if formula_name == formula_name_to_find:
                return formula_id
        return None

    def get_corresponding_formula(self, formula_id):
        """
        Get the Formulas which have id match with the given formula_id

        :param tuple formula_id: Key corresponding to a Formula
        :return: All Formulas that match with the key
        :rtype: list(Formula)
        """
        return self.formula_tree.get(formula_id)

    def remove_formula(self, formula_name_to_remove: str):
        """
        remove from the pool the formula with the given address
        :param formula_address_to_remove: address of the formula to remove
        :raise AttributeError: if the pool doesn't contain any formula with this address
        """
        formula_id_to_remove = None
        for formula_id, formula_name in self.formula_name.items():
            if formula_name_to_remove == formula_name:
                formula_id_to_remove = formula_id
        if formula_id_to_remove is not None:
            del self.formula_name[formula_id_to_remove]
        else:
            raise AttributeError
