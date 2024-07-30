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

import numpy as np

from .metrics import Bandwidth


class SweepResults:
    """
    Holds prediction results for a single benchmark, for all tested Ins_ooo parameters.
    Calculates mean, min, max of desired statistics (e.g. total cycles, IPC)
    """

    def __init__(self):
        # Dictionaries that map Insooo to predicted metric for that Insooo
        self.cycles = {}
        self.instructions = {}
        self.IPC = {}
        self.CPI = {}
        self.target_bws = {}

    def add_prediction(
        self,
        Insooo: float,
        predicted_cycles: int,
        predicted_instructions: int
    ) -> None:
        """
        Add a prediction for a given Insooo.

        Args:
            Insooo (float): Insooo parameter for which the prediction was made.
            predicted_cycles (int): predicted total cycles.
            predicted_instructions (int): predicted total instructions.

        Returns:
            None
        """
        self.cycles[Insooo] = predicted_cycles
        self.instructions[Insooo] = predicted_instructions
        self.IPC[Insooo] = predicted_instructions / predicted_cycles
        self.CPI[Insooo] = predicted_cycles / predicted_instructions

    def aggregate_results(self) -> None:
        """ Aggregate results for all Insooo parameters. """
        self.mean_IPC = np.mean(list(self.IPC.values()), dtype=np.float128)
        self.min_IPC = min(list(self.IPC.values()))
        self.max_IPC = max(list(self.IPC.values()))
        self.mean_CPI = np.mean(list(self.CPI.values()), dtype=np.float128)
        self.min_CPI = min(list(self.CPI.values()))
        self.max_CPI = max(list(self.CPI.values()))

    def add_target_bandwidths(self, Insooo: float, bws: list[Bandwidth]):
        self.target_bws[Insooo] = bws
