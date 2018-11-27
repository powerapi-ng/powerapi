import os

from smartwatts.formula import ActorTestFormula
from smartwatts.test.test_actor_utility import CreationMessage, DeathMessage, SignedMessage


class MockedFormula(ActorTestFormula):
    """
    Formula that forward received message and notify its message interceptor
    when initialized or termianted
    """

    def __init__(self, name, message_interceptor, verbose=False):
        ActorTestFormula.__init__(self, name, message_interceptor, verbose=verbose)


    def init_actor(self):
        """ notify the message interceptor that this actor have been created"""
        ActorTestFormula.init_actor(self)
        msg = CreationMessage(os.getpid())
        self.pusher.send(msg)

    def initial_receive(self, msg):
        """ forward the message to the message interceptor"""
        signed_msg = SignedMessage(os.getpid(), msg)
        self.pusher.send(signed_msg)


    def terminated_behaviour(self):
        """ notify the message interceptor that this actor is dead"""
        msg = DeathMessage(os.getpid())
        self.pusher.send(msg)
