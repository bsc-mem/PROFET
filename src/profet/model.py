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

from . import curves
from .app_profile import Sample
from .metrics import Bandwidth


class MLPisNaNError(Exception):
    """ Raised when MLP is NaN. """
    def __str__(self):
        return f'MLP is NaN.'


class ResultNotConvergingError(Exception):
    """ Raised when bisection method does not converge. """
    def __str__(self):
        return ('Cannot find intersection between analytical and target '
                'bandwidth-latency curve because bisection does not converge.')


class SmallerCPIError(Exception):
    """ Raised when CPI is smaller than the minimum CPI. """
    def __init__(self, CPI_tot, BW_used, IPC_max):
        self.CPI_tot = CPI_tot
        self.BW_used = BW_used
        self.CPI_min = 1 / IPC_max

    def __str__(self):
        return f'CPI {self.CPI_tot} is smaller than the minimum CPI ({self.CPI_min})'


def calc_perf(cpu_config: dict, baseline_bwlat_curves: curves.Curves, target_bwlat_curves: curves.Curves,
              sample: Sample, Ins_ooo_percentage_def: float, display_warnings: bool = True) -> tuple[float, float]:
    """
    Calculates performance on a new memory configuration.
    Iterate to find bandwidth on different memory configuration.
    
    Args:
        cpu_config_path (str): CPU configuration file path.
        baseline_bwlat_curves (Curves): baseline bandwidth-latency curves object.
        target_bwlat_curves (Curves): target bandwidth-latency curves object.
        sample (Sample): application profile sample object.
        Ins_ooo_percentage_def (float): defined percentage of i_ooo parameter.
        display_warnings (bool, optional): display warnings. Defaults to True.

    Returns:
        A tuple containing the predicted CPI and bandwidth used on the
        target memory configuration.
    """
    BW_mbs_used_1 = sample.bw.value
    Ratio_RW_1 = sample.read_ratio
    Cyc_tot_1 = sample.cycles
    Miss_LLC = sample.llc_misses
    Ins_tot_1 = sample.instructions

    # Assign appropriate CPU config values for ROB, IPC_max, Lat_LLC and MSHR
    Ins_ROB = cpu_config["Ins_ROB"]
    IPC_max = cpu_config["IPC_max"]
    Lat_LLC = cpu_config["Lat_LLC"]
    MSHR = cpu_config["MSHR"]

    # Find Lat_mem^(1) from BW_used^(1) and Ratio_RW
    Lat_cyc_mem_1 = baseline_bwlat_curves.get_lat(Ratio_RW_1, sample.bw).value

    # llc_miss_distance_ins = Ins_tot_1 / Miss_LLC
    # llc_miss_distance_cyc = Cyc_tot_1 / Miss_LLC
    misses_per_ins = Miss_LLC / Ins_tot_1
    pen_mem_1 = Lat_cyc_mem_1 - Lat_LLC
    IPC_tot_1 = Ins_tot_1 / Cyc_tot_1
    CPI_tot_1 = Cyc_tot_1 / Ins_tot_1
    try:
        if CPI_tot_1 < 1 / IPC_max:
            raise SmallerCPIError(CPI_tot_1, BW_mbs_used_1, IPC_max)
    except SmallerCPIError as e:
        if display_warnings:
            print(e)
        CPI_tot_1 = 1 / IPC_max

    # Ins_ooo upper limit, equation 10
    Ins_ooo_percentage_max = pen_mem_1 * IPC_tot_1 * 1 / Ins_ROB

    if Ins_ooo_percentage_max > 1.:
        Ins_ooo_percentage_max = 1.0

    # Ins_ooo parameter lower limit
    Ins_ooo_percentage_min = 0.0

    # Perform sensitivity analysis on Ins_ooo, using Ins_ooo_percentage_def
    # parameter (goes from 0 to 1 in 10 steps)
    max_min_diff = (Ins_ooo_percentage_max - Ins_ooo_percentage_min)
    Ins_ooo_percentage = Ins_ooo_percentage_min + Ins_ooo_percentage_def * max_min_diff

    # MLP, point estimate, equation 15
    MLP_pe = 1. + Ins_ooo_percentage * Ins_ROB * misses_per_ins

    # calculate MLP_min, using sweep analysis for CPI_iter from 1/IPC_max to CPI_tot_1, in 10 steps
    # CPI_iter in the paper is CPI_0, the CPI in case of full LLC hits
    # We do not know its values but we do know the bounds
    MLP_min, MLP_max = np.inf, -np.inf
    for CPI_iter in np.linspace(1 / IPC_max, CPI_tot_1, 10):
        MLP_iter_up = (misses_per_ins * (pen_mem_1 - CPI_iter * Ins_ooo_percentage * Ins_ROB))
        MLP_iter_down = (CPI_tot_1 - CPI_iter)
        if MLP_iter_down == 0:
            # If CPI_iter is equal CPI_tot_1, means that we have no misses
            if MLP_iter_up > 0:
                MLP_iter = np.inf
            else:
                MLP_iter = -np.inf
        else:
            MLP_iter = MLP_iter_up / MLP_iter_down
        MLP_min = min(MLP_iter, MLP_min)
        MLP_max = max(MLP_iter, MLP_max)

    # The MSHR size limits the number of misses concurrently tracked
    MLP_min = min(MSHR, MLP_min)
    MLP_max = min(MSHR, MLP_max)

    # To make the MLP fit inside the boundaries
    MLP = min(max([MLP_pe, MLP_min]), MLP_max)

    if np.isnan(MLP):
        raise MLPisNaNError

    # Calculate CPI_tot_2 on the target memory configuration, using bisection method
    # Initialize bisection control variables
    bisection_error = np.inf
    target_max_bw = target_bwlat_curves.get_max_bw(Ratio_RW_1, unit='MBps').value
    bisection_upper_limit = target_max_bw
    bisection_lower_limit = 0
    iter_count = 0
    # Perform the bisection method
    while bisection_error > 0.01:
        if iter_count > 1500:
            # The result is not converging: it may happen in rare cases
            raise ResultNotConvergingError

        bw_iteration = (bisection_lower_limit + bisection_upper_limit) / 2
        # Get lat on the target system from bw-lat curves for the given rw-ratio and bw
        try:
            Lat_mem_2 = target_bwlat_curves.get_lat(Ratio_RW_1,
                                                    Bandwidth(bw_iteration, 'MBps')).value
        except curves.OvershootError:
            # We are targeting the BwLat curve beyond max recorded bw, on the right side of the curve
            # The intersection cannot be right of the current bw_iteration value
            # Therefore, we select the left half for the next iteration
            bisection_upper_limit = bw_iteration
            # We set bisection_error to a high number because the intersection
            # is for sure not at this point
            bisection_error = np.inf
            iter_count += 1
            continue

        # Calculate CPI_tot_2 and BW_mbs_used_2, equations 16 and 18
        CPI_tot_2 = CPI_tot_1 + misses_per_ins * 1 / MLP * (Lat_mem_2 - Lat_cyc_mem_1)
        BW_mbs_used_2 = BW_mbs_used_1 * CPI_tot_1 / CPI_tot_2

        # Calculate bisection control variables for the next iteration
        iter_count += 1
        bisection_error = abs(bw_iteration - BW_mbs_used_2)
        if (BW_mbs_used_2 < bw_iteration and BW_mbs_used_2 > 0):
            bisection_upper_limit = bw_iteration
        else:
            bisection_lower_limit = bw_iteration

    if BW_mbs_used_2 < 0 or BW_mbs_used_2 > target_max_bw:
        raise ValueError

    if CPI_tot_2 < 1 / IPC_max:
        raise SmallerCPIError(CPI_tot_2, BW_mbs_used_2, IPC_max)

    return CPI_tot_2, BW_mbs_used_2