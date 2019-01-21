

# Formula
formula_factory = (lambda name, verbose:
                   RAPLFormulaActor(name, pusher, verbose=verbose))

# Dispatcher
dispatcher = DispatcherActor('dispatcher', formula_factory,
                             verbose=args.verbose)
dispatcher.group_by(HWPCReport, HWPCGroupBy(getattr(HWPCDepthLevel,
                                                    args.hwpc_group_by),
                                            primary=True))
