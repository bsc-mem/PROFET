################################################################################
# Copyright (c) 2023, Barcelona Supercomputing Center
#                     Contact: mariana.carmin [at] bsc [dot] es
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.

#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.

#     * Neither the name of the copyright holder nor the names
#       of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################

from dataclasses import dataclass
import numbers


@dataclass(frozen=True)
class Frequency:
    value: float
    unit: str

    @property
    def valid_units(self) -> dict:
        return {
            'Hz': 1,
            'kHz': 1e3,
            'MHz': 1e6,
            'GHz': 1e9,
            'THz': 1e12,
        }

    def __post_init__(self):
        self.check_valid_unit(self.unit)
        
    def value_in(self, target_unit: str) -> float:
        """
        Gives the value converted from one unit to another.

        Args:
            target_unit (str): units of the output frequency values
                (see self.valid_units).

        Returns:
            float: value converted target_unit.
        """
        if self.unit == target_unit:
            return self.value
        self.check_valid_unit(target_unit)
        # Convert the input value to Hz
        value_hz = self.value * self.valid_units[self.unit]
        # Convert the value in Hz to the desired output unit
        return value_hz / self.valid_units[target_unit]
    
    def as_unit(self, target_unit: str) -> 'Frequency':
        """
        Gives the frequency with the value converted from one unit to another.

        Args:
            target_unit (str): units of the output frequency values
                (see self.valid_units).

        Returns:
            Frequency: new Frequency object with the converted value and units.
        """
        converted_value = self.value_in(target_unit)
        return Frequency(converted_value, target_unit)
    
    def check_valid_unit(self, unit: str) -> None:
        if unit not in self.valid_units.keys():
            raise Exception(f'Frequency units {unit} not supported. '
                            'Supported units are {self.valid_units.keys()}.')


@dataclass(frozen=True)
class Bandwidth:
    value: float
    unit: str

    @property
    def valid_units(self) -> dict:
        return {
            # 'B/s': 1,
            # 'KB/s': 1e3,
            # 'MB/s': 1e6,
            # 'GB/s': 1e9,
            # 'TB/s': 1e12,
            'Bps': 1,
            'KBps': 1e3,
            'MBps': 1e6,
            'GBps': 1e9,
            'TBps': 1e12,
        }

    def __post_init__(self):
        self.check_valid_unit(self.unit)
    
    def value_in(self, target_unit: str) -> float:
        """
        Gives the value converted from one unit to another.

        Args:
            target_unit (str): units of the output bandwidth values
                (see self.valid_units).

        Returns:
            float: value converted target_unit.
        """
        if self.unit == target_unit:
            return self.value
        self.check_valid_unit(target_unit)
        # Convert the input value to bytes per second (B/s)
        value_Bps = self.value * self.valid_units[self.unit]
        # Convert the value in Bps to the desired output unit
        return value_Bps / self.valid_units[target_unit]

    def as_unit(self, target_unit: str) -> 'Bandwidth':
        """
        Gives the bandwidth with the value converted from one unit to another.

        Args:
            target_unit (str): units of the output bandwidth values
            (see self.valid_units).

        Returns:
            Bandwidth: new Bandwidth object with the converted value and units.
        """
        converted_value = self.value_in(target_unit)
        return Bandwidth(converted_value, target_unit)
    
    def check_same_unit(self, other: 'Bandwidth') -> None:
        if self.unit != other.unit:
            raise Exception('Bandwidth units are not the same '
                            f'(current={self.unit}, other={other.unit}).')
    
    def check_unit(self, unit: str) -> None:
        if self.unit != unit:
            raise Exception('Bandwidth units are not the same '
                            f'(current={self.unit} vs {unit}).')
  
    def check_valid_unit(self, unit: str) -> None:
        if unit not in self.valid_units.keys():
            raise Exception(f'Bandwidth units {unit} not supported. '
                            f'Supported units are {self.valid_units.keys()}.')
    
    def __add__(self, other: 'Bandwidth') -> 'Bandwidth':
        if self.unit != other.unit:
            raise Exception('Cannot add bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return Bandwidth(self.value + other.value, self.unit)
    
    def __sub__(self, other: 'Bandwidth') -> 'Bandwidth':
        if self.unit != other.unit:
            raise Exception('Cannot subtract bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return Bandwidth(self.value - other.value, self.unit)
    
    def __mul__(self, other: numbers.Number) -> 'Bandwidth':
        return Bandwidth(self.value * other, self.unit)
    
    def __truediv__(self, other: numbers.Number) -> 'Bandwidth':
        return Bandwidth(self.value / other, self.unit)
    
    def __floordiv__(self, other: numbers.Number) -> 'Bandwidth':
        return Bandwidth(self.value // other, self.unit)
    
    def __mod__(self, other: numbers.Number) -> 'Bandwidth':
        return Bandwidth(self.value % other, self.unit)
    
    def __pow__(self, other: numbers.Number) -> 'Bandwidth':
        return Bandwidth(self.value ** other, self.unit)
    
    def __eq__(self, other: 'Bandwidth') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value == other.value
    
    def __ne__(self, other: 'Bandwidth') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value != other.value
    
    def __lt__(self, other: 'Bandwidth') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value < other.value
    
    def __le__(self, other: 'Bandwidth') -> bool:
        if isinstance(other, Bandwidth):
            if self.unit != other.unit:
                raise Exception('Cannot compare bandwidths with different units '
                                f'({self.unit} and {other.unit}).')
            return self.value <= other.value
    
    def __gt__(self, other: 'Bandwidth') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare bandwidths with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value > other.value
    
    def __ge__(self, other: 'Bandwidth') -> bool:
        if isinstance(other, Bandwidth):
            if self.unit != other.unit:
                raise Exception('Cannot compare bandwidths with different units '
                                f'({self.unit} and {other.unit}).')
            return self.value >= other.value
    
    def __str__(self) -> str:
        return f'{self.value:.2f} {self.unit}'
    
    def __repr__(self) -> str:
        return f'Bandwidth({self.value}, {self.unit})'
    

@dataclass(frozen=True)
class Latency:
    value: float
    unit: str

    @property
    def valid_units(self) -> dict:
        return {
            'cycles': 1,
            's': 1,
            'ms': 1e3,
            'us': 1e6,
            'ns': 1e9,
        }

    def __post_init__(self):
        self.check_valid_unit(self.unit)

    def value_in(self, target_unit: str, freq: Frequency = None) -> float:
        """
        Gives the value converted from one unit to another.

        Args:
            to_unit (str): units of the output latency values
                (see supported_lat_units()).
            freq (Frequency, optional): CPU frequency, only necessary
                when converting to or from 'cycles'. Defaults to None.
        
        Returns:
            float: value converted target_unit.
        """
        if self.unit == target_unit:
            return self.value

        self.check_valid_unit(target_unit)
        if self.unit == 'cycles' or target_unit == 'cycles':
            if freq is None:
                raise Exception(f'Frequency must be provided when any of the '
                                'latency units are in cycles.')
            if freq.unit != 'GHz':
                # Make sure the frequency is in GHz
                freq = freq.as_unit('GHz')

        if self.unit == 'cycles':
            # From cycles to time
            cyc_per_sec = freq.value * 1e9
            sec = self.value / cyc_per_sec
            return sec * self.valid_units[target_unit]
        elif target_unit == 'cycles':
            # From time to cycles
            cyc_per_sec = freq.value * 1e9
            sec = self.value / self.valid_units[self.unit]
            return sec * cyc_per_sec
        else:
            # From time to time
            t2t = self.valid_units[self.unit] * self.valid_units[target_unit]
            return self.value / t2t

    def as_unit(self, target_unit: str, freq: Frequency = None) -> 'Latency':
        """
        Gives the latency with the value converted from one unit to another.

        Args:
            target_unit (str): units of the output latency values
                (see self.valid_units).
            freq (Frequency, optional): CPU frequency, only necessary
                when converting to or from 'cycles'. Defaults to None.

        Returns:
            Latency: new Latency object with the converted value and units.
        """
        converted_value = self.value_in(target_unit, freq)
        return Latency(converted_value, target_unit)
    
    def check_same_unit(self, other: 'Latency') -> None:
        if self.unit != other.unit:
            raise Exception('Latency units are not the same '
                            f'(current={self.unit}, other={other.unit}).')
        
    def check_valid_unit(self, unit: str) -> None:
        if unit not in self.valid_units.keys():
            raise Exception(f'Latency units {unit} not supported. Supported '
                            'units are {self.valid_units.keys()}.')
    
    def __add__(self, other: 'Latency') -> 'Latency':
        if self.unit != other.unit:
            raise Exception('Cannot add latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return Latency(self.value + other.value, self.unit)
    
    def __sub__(self, other: 'Latency') -> 'Latency':
        if self.unit != other.unit:
            raise Exception('Cannot subtract latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return Latency(self.value - other.value, self.unit)
    
    def __mul__(self, other: numbers.Number) -> 'Latency':
        return Latency(self.value * other, self.unit)
    
    def __truediv__(self, other: numbers.Number) -> 'Latency':
        return Latency(self.value / other, self.unit)
    
    def __floordiv__(self, other: numbers.Number) -> 'Latency':
        return Latency(self.value // other, self.unit)
    
    def __mod__(self, other: numbers.Number) -> 'Latency':
        return Latency(self.value % other, self.unit)
    
    def __pow__(self, other: numbers.Number) -> 'Latency':
        return Latency(self.value ** other, self.unit)
    
    def __eq__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value == other.value
    
    def __ne__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value != other.value
    
    def __lt__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value < other.value
    
    def __le__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value <= other.value
    
    def __gt__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value > other.value
    
    def __ge__(self, other: 'Latency') -> bool:
        if self.unit != other.unit:
            raise Exception('Cannot compare latencies with different units '
                            f'({self.unit} and {other.unit}).')
        return self.value >= other.value
    
    def __str__(self) -> str:
        return f'{self.value:.2f} {self.unit}'
    
    def __repr__(self) -> str:
        return f'Latency({self.value}, {self.unit})'
        