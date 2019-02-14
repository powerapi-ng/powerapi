from powerapi import DispatcherActor

# Create the dispatcher with the formula_factory
dispatcher = DispatcherActor('dispatcher', formula_factory)

# Create a first rule of dispatch_rule with...
# the report type and the dispatch_rule rule
dispatcher.dispatch_rule(HWPCReport, HWPCDispatchRule(HWPCDepthLevel.SOCKET,
                                            primary=True))
