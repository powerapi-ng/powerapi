from smartwatts import XXXFormulaActor

# With basic function
def my_factory(name, verbose):
    return XXXFormulaActor(name, ..., verbose=verbose)
formula_factory = my_factory

# With lambda expression
formula_factory = (lambda name, verbose:
                   XXXFormulaActor(name, ..., verbose=verbose))
