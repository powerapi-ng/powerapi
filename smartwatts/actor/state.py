class BasicState:
    """
    A basic state class that encapsulate basic actor values :

    :attribute boolean initialized: True if the actor is initialized and can
                                    handle all messages, False otherwise
    :attribute boolean alive: True if the actor is alive, False otherwise
    :attribute behaviour: function that implement the basic behaviour
    :type behaviour: (fun (actor) -> None)
    :attribute socket_interface: communication interface of the actor
    :type socket_interface: smartwatts.actor.socket_interface.SocketInterface
    """

    def __init__(self, behaviour, socket_interface):
        """
        :param behaviour: function that implement the basic behaviour
        :type behaviour: (fun (actor) -> None)
        :param socket_interface: communication interface of the actor
        :type socket_interface: smartwatts.actor.socket_interface.SocketInterface
        """

        self.initialized = False
        self.alive = True
        self.socket_interface = socket_interface
        self.behaviour = behaviour
