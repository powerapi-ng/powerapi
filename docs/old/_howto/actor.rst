.. How to create an Actor

un nouveau ``powerapi.Actor``
-------------------------------------

Tutoriel de création d'un ``Actor``.

* ``MyClassState`` héritant de ``BasicState`` 

  * BasicState.__init__(self, behaviour, socket_interface)
  * Others values

* ``MyClassActor`` héritant de ``Actor``

  * dans __init__

    * Actor.__init__(self, name, verbose)
    * self.state = ``MyClassState``

  * Override...

    * ``setup``: call Actor setup and Link Message to Handler

  * Can override...

    * ``terminated_behaviour``: Si besoin d'ajouter des opérations au moment de la mort 
    * ``_initial_behaviour``: Pour changer le comportement par défaut
