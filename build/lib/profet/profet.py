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

import json

from . import model
from . import curves
from .sweep_results import SweepResults
from .curves import Curves
from .metrics import Bandwidth
from .app_profile import AppProfile


def estimate_profiling_samples(app_profile: AppProfile, cpu_config: dict, baseline_curves: Curves, target_curves: Curves,
                               Ins_ooo_percentage: float, display_warnings: bool = True) -> dict:
    """
    Goes trough the traces and calls the functions to calculate
    performance estimations based on the given Ins_ooo_percentage.

    Args:
        app_profile (AppProfile): directory containing the application profiling (Str).
        cpu_config (str): directory containing the CPU configuration file.
        baseline_curves (Curves): Curves class for the baseline memory system.
        target_curves (Curves): Curves class for the target memory system.
        Ins_ooo_percentage (float): percentage of instructions that can be executed out of order.
        display_warnings (bool, optional): if True, warnings are displayed.

    Returns:
        Dict with the lists of cycles, instructions, sampled read ratios,
        and target bandwidths for each sample in the application profiling.
    """
    # Lists of cycles, instructions and target BWs
    est = {
        'Cyc_2': [],
        'Ins_2': [],
        'BWs_2': [],
    }

    # If a prediction is not possible, we use prediction of the previous sample
    # Initialize BW and CPI predictions before processing the first sample
    prev_BW_used_2 = 0
    prev_CPI_tot_2 = 1

    for sample in app_profile:
        # Calculate performance estimation
        try:
            CPI_tot_2, BW_used_2 = model.calc_perf(cpu_config,
                                                   baseline_curves,
                                                   target_curves,
                                                   sample,
                                                   Ins_ooo_percentage,
                                                   display_warnings)
            est['BWs_2'].append(Bandwidth(BW_used_2, 'MBps'))
        # TODO IB: I'm not sure we should handle this exceptions and set a value for CPI_tot_2 and BW_used_2.
        # TODO IB: Probably a better option would be to ignore these instances and show warnings?
        except curves.OvershootError as e:
            if display_warnings:
                print(e)
            CPI_tot_2 = prev_CPI_tot_2
            BW_used_2 = prev_BW_used_2
        except (model.MLPisNaNError, model.ResultNotConvergingError) as e:
            if display_warnings:
                print(f'Warning: Cannot predict performance for sample {sample}.')
                print(e)
            CPI_tot_2 = prev_CPI_tot_2
            BW_used_2 = prev_BW_used_2
        except model.SmallerCPIError as e:
            if display_warnings:
                print(e)
            CPI_tot_2 = e.CPI_min
            BW_used_2 = e.BW_used

        est['Cyc_2'].append(CPI_tot_2 * sample.instructions)
        est['Ins_2'].append(sample.instructions)
        prev_BW_used_2 = BW_used_2
        prev_CPI_tot_2 = CPI_tot_2

    return est


def estimate_performance(
    app_profile: AppProfile,
    cpu_config: dict,
    baseline_curves: Curves,
    target_curves: Curves,
    display_warnings: bool = True
) -> dict:
    """
    Goes trough the traces and calls the functions to calculate
    performance estimations, sweeping different values of Ins_ooo_percentage.

    **Direct Usage**:

    This function is available directly from the `profet` module for convenience.

    .. code-block:: python

        import profet
        result = profet.estimate_performance(arg1, arg2, ...)

    Args:
        app_profile (AppProfile): directory containing the application profiling (Str).
        cpu_config (dict): CPU configuration data.
        baseline_curves (Curves): Curves class for the baseline memory system.
        target_curves (Curves): Curves class for the target memory system.
        display_warnings (bool, optional): if True, warnings are displayed.

    Returns:
        Dictionary containing the results of the performance estimation.
    """

    # We use nomenclature as introduced in the paper
    # Note: Cyc_tot, total reffers to Cyc_0+Cyc_LLC, not total cycles for the whole app
    # We use keyword "overall" to refer to numbers for the whole app (all samples)

    sweep_results = SweepResults()
    # Perform sensitivity analysis for Ins_ooo: from min to max using 10% step
    for Ins_ooo_percentage in (0., .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.):
        estimations = estimate_profiling_samples(app_profile, cpu_config,
                                                 baseline_curves, target_curves,
                                                 Ins_ooo_percentage, display_warnings)
        sweep_results.add_prediction(Ins_ooo_percentage,
                                     sum(estimations['Cyc_2']),
                                     sum(estimations['Ins_2']))
        sweep_results.add_target_bandwidths(Ins_ooo_percentage,
                                            estimations['BWs_2'])

    # Final result is the average of sensitivity (sweep) analysis
    # Calculate mean, min and max predicted IPC for the whole benchmark on system 2 (target)
    sweep_results.aggregate_results()

    result = {}
    # Calculate performance (IPC) diff relative to the measured IPC on the baseline system
    result['IPC.base'] = app_profile.total_IPC
    result['IPC.target'] = sweep_results.mean_IPC
    result['IPC.change.avg'] = (sweep_results.mean_IPC / app_profile.total_IPC - 1.) * 100.
    # Calculate error bars
    # (distance from min/max IPC diff. rel. to measured IPC to mean IPC diff. rel. to measured IPC)
    min_ipc_ratio = sweep_results.min_IPC / app_profile.total_IPC - 1.
    max_ipc_ratio = sweep_results.max_IPC / app_profile.total_IPC - 1.
    mean_ipc_ratio = sweep_results.mean_CPI / app_profile.total_CPI - 1.
    min_cpi_ratio = sweep_results.min_CPI / app_profile.total_CPI - 1.
    max_cpi_ratio = sweep_results.max_CPI / app_profile.total_CPI - 1.

    result['IPC.change.min'] = result['IPC.change.avg'] - 100. * min_ipc_ratio
    result['IPC.change.max'] = 100. * max_ipc_ratio - result['IPC.change.avg']
    result['CPI.base'] = app_profile.total_CPI
    result['CPI.target'] = sweep_results.mean_CPI
    result['CPI.change.avg'] = mean_ipc_ratio * 100.
    result['CPI.change.min'] = result['CPI.change.avg'] - 100. * min_cpi_ratio
    result['CPI.change.max'] = 100. * max_cpi_ratio - result['CPI.change.avg']

    result['Target.BWs'] = estimations['BWs_2']

    return result