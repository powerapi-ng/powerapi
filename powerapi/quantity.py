# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
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

# Author : Daniel Romero Acero
# Last modified : 17 March 2022

##############################
#
# Imports
#
##############################
import pint
from pint import UnitRegistry

##############################
#
# Constants
#
##############################

unit_reg = UnitRegistry()
PowerAPIPint_MODULE_NAME = "pint"
PowerAPIPint = pint
PowerAPIUnit = pint.Unit
PowerAPIQuantity = pint.Quantity

# Power
W = unit_reg.watt
MW = unit_reg.megawatt
KW = unit_reg.kilowatt
mW = unit_reg.microwatt
DEFAULT_POWER_UNIT = W

# Frequency
Hz = unit_reg.hertz
MHz = unit_reg.megahertz
GHz = unit_reg.gigahertz
DEFAULT_FREQUENCY_UNIT = Hz

# Energy
J = unit_reg.joule
MJ = unit_reg.megajoule
KJ = unit_reg.kilojoule
mJ = unit_reg.microjoule
DEFAULT_ENERGY_UNIT = J

# Time
ms = unit_reg.ms
DEFAULT_TIME_UNIT = ms



##############################
#
# Function
#
##############################

def to_default_power_unit(quantity: PowerAPIQuantity):
    return quantity.to(DEFAULT_POWER_UNIT)


def to_default_frequency_unit(quantity: PowerAPIQuantity):
    return quantity.to(DEFAULT_FREQUENCY_UNIT)

