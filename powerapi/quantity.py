import pint
from pint.quantity import Quantity as PowerAPIQuantity

unit_reg = pint.UnitRegistry()
WATTS = unit_reg.watts
Hz = unit_reg.hertz
DEFAULT_POWER_UNIT = WATTS
DEFAULT_FREQUENCY_UNIT = Hz


def to_default_power_unit(quantity: PowerAPIQuantity):
    return quantity.to(DEFAULT_POWER_UNIT)


def to_default_frequency_unit(quantity: PowerAPIQuantity):
    return quantity.to(DEFAULT_FREQUENCY_UNIT)

