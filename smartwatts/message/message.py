"""
Module message
"""


class UnknowMessageTypeException(Exception):
    """
    Exception happen when we don't know the message type
    """
    pass


class PoisonPillMessage:
    """
    Class of message which allow to kill an actor
    """
    pass
