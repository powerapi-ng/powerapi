# Copyright (c) 2023, INRIA
# Copyright (c) 2023, University of Lille
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
from powerapi.actor import Actor
from powerapi.exception import MissingArgumentException, MissingValueException, BadInputData, \
    UnsupportedActorTypeException
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor

FROM_KEY = 'from'
TO_KEY = 'to'
PATH_SEPARATOR = '.'
INPUT_GROUP = 'input'
OUTPUT_GROUP = 'output'
PROCESSOR_GROUP = 'processor'
BINDING_GROUP = 'binding'


class BindingManager:
    """
    Class for management the binding between actors during their creation process
    """

    def __init__(self, actors: dict = {}):
        """
        :param dict actors: Dictionary of actors to create the bindings
        """
        self.actors = actors

    def process_bindings(self, bindings: dict):
        """
        Define bindings between self.actors according to the provided binding dictionary.
        """
        raise NotImplementedError()


def check_parameters_in_binding(binding: dict):
    """
    Check that a binding has the from and to parameters and that they have a value.
    If it is not the case, it raises a MissingArgumentException or
    """
    # Check from and to exist
    if FROM_KEY not in binding:
        raise MissingArgumentException(argument_name=FROM_KEY)

    if TO_KEY not in binding:
        raise MissingArgumentException(argument_name=TO_KEY)

    from_actor_path = binding[FROM_KEY]
    to_actor_path = binding[TO_KEY]

    # Check that from and to values are not empty
    if from_actor_path == "" or to_actor_path == "":
        raise MissingValueException(argument_name=FROM_KEY + ' or ' + TO_KEY)


class ProcessorBindingManager(BindingManager):
    """
    Class for management the binding between processor actors and others actors
    """

    def __init__(self, actors: dict):
        """
        The ProcessorBindingManager keeps an actor dictionary with  the following structure: [<group_name>][actor_name]
        where <group_name> is 'input' for pullers, 'output' for pushers and
        'processor' for processors
        :param dict actors: Dictionary of actors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        """

        BindingManager.__init__(self, actors={INPUT_GROUP: {}, OUTPUT_GROUP: {}, PROCESSOR_GROUP: {}})
        if actors:
            self.add_actors(actors=actors)

    def process_bindings(self, bindings: dict):
        """
        Define bindings between self.actors according to the provided binding dictionary.
        This dictionary has the structure
        {"<binding_name>":
            "from": "<from_actor_path>",
            "to": "<to_actor_path>"
        }
        the "<from_actor_path>" and "to": "<to_actor_path>" follow the convention "<subgroup_name>.<actor_name>"
        according to the configuration, e.g., "input.my_puller" and "processor.my_libvirt_processor"

        One of the actors in the binding hs to be a processor. If the "to" actor is the processor, the "from" has to be
        a puller. If the "from" actor is a processor, the "to" actor has to be a pusher.
        :param bindings: The bindings to be processed.
        """

        for _, binding in bindings.items():

            check_parameters_in_binding(binding=binding)

            from_actor_path = binding[FROM_KEY]
            to_actor_path = binding[TO_KEY]

            # Check that the paths have the correct format and the actors with the
            # given paths exist

            from_actor_path = self.check_actor_path(actor_path=from_actor_path)
            to_actor_path = self.check_actor_path(actor_path=to_actor_path)

            # Check that actors types are correct

            from_actor = self.actors[from_actor_path[0]][from_actor_path[1]]
            to_actor = self.actors[to_actor_path[0]][to_actor_path[1]]

            # Check types and do the processing
            if isinstance(from_actor, ProcessorActor):
                if not isinstance(to_actor, PusherActor):
                    raise BadInputData()

                # The processor has to be between the formula and the pusher
                # The pusher becomes a target of the processor
                processor = from_actor
                processor.add_target_actor(actor=to_actor)

                # We look for the pusher on each dispatcher in order to replace it by
                # the processor.
                for _, puller in self.actors[INPUT_GROUP]:
                    for filter in puller.state.report_filter.filters:
                        dispatcher = filter[1]

                        number_of_pushers = len(dispatcher.pusher)
                        pusher_updated = False

                        for index in range(number_of_pushers):
                            if dispatcher.pusher[index] == to_actor:
                                dispatcher.pusher[index] = processor
                                pusher_updated = True
                                break

                        if pusher_updated:
                            dispatcher.update_state_formula_factory()

            elif isinstance(to_actor, ProcessorActor):
                if not isinstance(from_actor, PullerActor):
                    raise BadInputData()

                # The processor has to be between the puller and the dispatcher
                # The dispatcher becomes a target of the processor

                # The dispatcher defines the relationship between the Formula and
                # puller
                processor = to_actor
                number_of_filters = len(from_actor.state.report_filter.filters)

                for index in range(number_of_filters):
                    # The filters define the relationship with the dispatcher
                    # The relationship has to be updated
                    current_filter = list(from_actor.state.report_filter.filters[index])
                    current_filter_dispatcher = current_filter[1]
                    processor.add_target_actor(actor=current_filter_dispatcher)
                    current_filter[1] = processor
                    from_actor.state.report_filter.filters[index] = tuple(current_filter)
            else:
                raise BadInputData()

    def add_actor(self, actor: Actor):
        """
        Add the actor to the dictionary of actors according to its type.
        Actor has to be PullerActor, PusherActor or ProcessorActor. The key of the actor is its name
        """
        group = None
        if isinstance(actor, PullerActor):
            group = INPUT_GROUP
        elif isinstance(actor, PusherActor):
            group = OUTPUT_GROUP
        elif isinstance(actor, ProcessorActor):
            group = PROCESSOR_GROUP
        else:
            raise UnsupportedActorTypeException(actor_type=str(type(actor)))

        self.actors[group][actor.name] = actor

    def add_actors(self, actors: dict):
        """
        Add the dictionary of actors to the manager dictionary
        """
        for _, actor in actors.items():
            self.add_actor(actor)

    def check_actor_path(self, actor_path: str):
        """
        Check that an actor path is separated by PATH_SEPARATOR, that it has to subpaths (group and actor name)
        and the actor exist in self.actors. It raises a BadInputData exception is these conditions are not respected.
        Otherwise, it returns the path in a list with two elements
        """

        path = actor_path.split(PATH_SEPARATOR)

        if len(path) != 2 or path[0] not in self.actors or path[1] not in self.actors[path[0]]:
            raise BadInputData()

        return path
