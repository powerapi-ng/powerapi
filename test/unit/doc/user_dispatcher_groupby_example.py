from powerapi import DispatcherActor

# Create the dispatcher with the formula_factory
dispatcher = DispatcherActor('dispatcher', formula_factory)

# Create a first rule of group_by with...
# the report type and the group_by rule
dispatcher.group_by(HWPCReport, HWPCGroupBy(HWPCDepthLevel.SOCKET,
                                            primary=True))
