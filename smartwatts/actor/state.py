class BasicState:
    """
    A basic state class that encapsulate basic actor values :

    alive(boolean): True if the actor is alive, False otherwise
    behaviour(fun (actor) -> unit): function that implement the basic behaviour
    the actor
    """

    def __init__(self, behaviour, socket_interface):
        """
        Parameters:
            behaviour(fun (actor) -> unit): function that implement the basic
        behaviour the actor
        """

        self.initialized = False
        self.socket_interface = socket_interface
        self.alive = True
        self.behaviour = behaviour
