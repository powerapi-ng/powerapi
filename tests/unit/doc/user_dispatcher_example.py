

# Formula
formula_factory = (lambda name, verbose:
                   RAPLFormulaActor(name, pusher, verbose=verbose))

# Dispatcher
dispatcher = DispatcherActor('dispatcher', formula_factory,
                             verbose=args.verbose)
dispatcher.dispatch_rule(HWPCReport, HWPCDispatchRule(getattr(HWPCDepthLevel,
                                                    args.hwpc_dispatch_rule),
                                            primary=True))
