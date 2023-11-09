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
# pylint: disable=R1702
from powerapi.exception import UnsupportedActorTypeException, UnexistingActorException, TargetActorAlreadyUsed
from powerapi.processor.processor_actor import ProcessorActor
from powerapi.puller import PullerActor
from powerapi.pusher import PusherActor


class BindingManager:
    """
    Class for management the binding between actors during their creation process
    """

    def __init__(self, actors: dict = {}):
        """
        :param dict actors: Dictionary of actors to create the bindings. The name of the actor is the key
        """
        if not actors:
            self.actors = {}
        else:
            self.actors = actors

    def process_bindings(self):
        """
        Define bindings between self.actors according to the processors' targets.
        """
        raise NotImplementedError()


class ProcessorBindingManager(BindingManager):
    """
    Class for management of bindings between processor actors and others actors
    """

    def __init__(self, actors: dict, processors: dict):
        """
        The ProcessorBindingManager defines bindings between actors and processors
        :param dict actors: Dictionary of actors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        :param dict processors: Dictionary of processors with structure {<processor1_key>:processor1,
        <processor2_key>:processor2...}
        """

        BindingManager.__init__(self, actors=actors)
        if not processors:
            self.processors = {}
        else:
            self.processors = processors

    def check_processor_targets(self, processor: ProcessorActor):
        """
        Check that targets of a processor exist in the dictionary of targets.
        If it is not the case, it raises a UnexistingActorException
        """
        for target_actor_name in processor.state.target_actors_names:
            if target_actor_name not in self.actors:
                raise UnexistingActorException(actor=target_actor_name)

    def check_processors_targets_are_unique(self):
        """
        Check that processors targets are unique, i.e., the same target is not related to
        two different processors
        """
        used_targets = []
        for _, processor in self.processors.items():
            for target_actor_name in processor.state.target_actors_names:
                if target_actor_name in used_targets:
                    raise TargetActorAlreadyUsed(target_actor=target_actor_name)
                else:
                    used_targets.append(target_actor_name)


class PreProcessorBindingManager(ProcessorBindingManager):
    """
    Class for management the binding between pullers and pre-processor actors
    """

    def __init__(self, pullers: dict, processors: dict):
        """
        The PreProcessorBindingManager defines bindings between pullers and processors: puller->processor->dispatcher
        :param dict pullers: Dictionary of actors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        :param dict processors: Dictionary of processors with structure {<processor1_key>:processor1,
        <processor2_key>:processor2...}
        """

        ProcessorBindingManager.__init__(self, actors=pullers, processors=processors)

    def process_bindings(self):
        """
        Define bindings between self.actors according to the pre-processors' targets.

        """

        # Check that processors targets are unique
        self.check_processors_targets_are_unique()

        # For each processor, we get targets and create the binding:
        # puller->processor->dispatcher
        for _, processor in self.processors.items():

            self.check_processor_targets(processor=processor)

            for target_actor_name in processor.state.target_actors_names:

                # The processor has to be between the puller and the dispatcher
                # The dispatcher becomes a target of the processor

                puller_actor = self.actors[target_actor_name]

                # The dispatcher defines the relationship between the Formula and
                # Puller
                number_of_filters = len(puller_actor.state.report_filter.filters)

                for index in range(number_of_filters):
                    # The filters define the relationship with the dispatcher
                    # The relationship has to be updated
                    current_filter = list(puller_actor.state.report_filter.filters[index])
                    current_filter_dispatcher = current_filter[1]
                    processor.add_target_actor(actor=current_filter_dispatcher)
                    current_filter[1] = processor
                    puller_actor.state.report_filter.filters[index] = tuple(current_filter)

    def check_processor_targets(self, processor: ProcessorActor):
        """
        Check that targets of a processor exist in the dictionary of targets.
        If it is not the case, it raises a UnexistingActorException
        It also checks that the actor is a PullerActor instance.
        If it is not the case, it raises UnsupportedActorTypeException
        """
        ProcessorBindingManager.check_processor_targets(self, processor=processor)

        for target_actor_name in processor.state.target_actors_names:
            actor = self.actors[target_actor_name]

            if not isinstance(actor, PullerActor):
                raise UnsupportedActorTypeException(actor_type=type(actor).__name__)


class PostProcessorBindingManager(ProcessorBindingManager):
    """
    Class for management the binding between post-processor and pusher actors
    """

    def __init__(self, pushers: dict, processors: dict, pullers: dict):
        """
        The PostProcessorBindingManager defines bindings between processors and pushers: formula->processor->pushers
        :param dict pushers: Dictionary of PusherActors with structure {<actor1_key>:actor1,<actor2_key>:actor2...}
        :param dict processors: Dictionary of processors with structure {<processor1_key>:processor1,
        <processor2_key>:processor2...}
        """
        ProcessorBindingManager.__init__(self, actors=pushers, processors=processors)
        self.pullers = pullers

    def process_bindings(self):
        """
        Define bindings between self.actors according to the post-processors' targets.

        """

        # For each processor, we get targets and create the binding:
        # formula->processor->pusher
        for _, processor in self.processors.items():

            self.check_processor_targets(processor=processor)

            for target_actor_name in processor.state.target_actors_names:

                # The processor has to be between the formula and the pusher
                # The pusher becomes a target of the processor

                pusher_actor = self.actors[target_actor_name]

                processor.add_target_actor(actor=pusher_actor)

                # We look for the pusher on each dispatcher in order to replace it by
                # the processor
                for _, puller in self.pullers:

                    for current_filter in puller.state.report_filter.filters:
                        dispatcher = current_filter[1]

                        number_of_pushers = len(dispatcher.pusher)
                        pusher_updated = False

                        for index in range(number_of_pushers):
                            if dispatcher.pusher[index] == pusher_actor:
                                dispatcher.pusher[index] = processor
                                pusher_updated = True
                                break

                        if pusher_updated:
                            dispatcher.update_state_formula_factory()

    def check_processor_targets(self, processor: ProcessorActor):
        """
        Check that targets of a processor exist in the dictionary of targets.
        If it is not the case, it raises a UnexistingActorException
        It also checks that the actor is a PusherActor instance.
        If it is not the case, it raises UnsupportedActorTypeException
        """
        ProcessorBindingManager.check_processor_targets(self, processor=processor)

        for target_actor_name in processor.state.target_actors_names:
            actor = self.actors[target_actor_name]

            if not isinstance(actor, PusherActor):
                raise UnsupportedActorTypeException(actor_type=type(actor).__name__)
