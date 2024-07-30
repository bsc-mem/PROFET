#!/usr/bin/env python3

################################################################################
# Copyright (c) 2023, Valéria S. Girelli
#                     Pouya Esmaili
#                     Mariana Carmin
#                     Petar Radojkovic
#                     Paul Carpenter
#                     Eduard Ayguade
#                     Contact: valeria.soldera [at] bsc [dot] es
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of the copyright holder nor the names
#       of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
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

import os
import argparse
import json
from src.metrics import Bandwidth, Latency
from src.sweep_results import SweepResults
from src.curves import Curves
from src.app_profile import AppProfile
from src.results import Results
import src.results as results
import src.utils as utils
import src.visualization as viz
import src.model as model
import src.curves as curves
import numpy as np

__version__ = "1.0"
__status__ = "Release"

def estimate_profiling_samples(app_profile: AppProfile, cpu_config: dict, baseline_curves: Curves, target_curves: Curves,
                               Ins_ooo_percentage: float, display_warnings: bool = True) -> tuple[list[float], list[float]]:
    """
    Goes trough the traces and calls the functions to calculate performance estimations based on the given Ins_ooo_percentage.

    Args:
        app_profile (AppProfile): directory containing the application profiling (Str)
        cpu_config (str): directory containing the CPU configuration file.
        baseline_curves (Curves): Curves class for the baseline memory system.
        target_curves (Curves): Curves class for the target memory system.
        Ins_ooo_percentage (float): percentage of instructions that can be executed out of order.
        display_warnings (bool): if True, warnings are displayed.

    Returns:
        Tuple with the lists of cycles and instructions for each sample in the application profiling.
    """
    # Lists of cycles. Instructions are also recorded to enable hadling impossible predictions
    Cyc_2 = []
    Ins_2 = []

    # If a prediction is not possible, we use prediction of the previous sample
    # Initialize BW and CPI predictions before processing the first sample
    prev_BW_used_2 = 0
    prev_CPI_tot_2 = 1
    index = 0
    BW_list=[]
    BW_list_baseline=[]
    Rd_list=[]
    for sample in app_profile:
        # Calculate performance estimation
        try:
            CPI_tot_2, BW_used_2 = model.calc_perf(cpu_config,
                                                    baseline_curves,
                                                    target_curves,
                                                    sample,
                                                    Ins_ooo_percentage,
                                                    display_warnings)
        # TODO IB: I'm not sure we should handle this exceptions and set a value for CPI_tot_2 and BW_used_2.
        # TODO Probably a better option would be to ignore these instances and show warnings?
            BW_list.append(Bandwidth(BW_used_2, 'MBps'))
            BW_list_baseline.append(sample.bw.value)
            Rd_list.append(sample.read_ratio)
            index+=1
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

        Cyc_2.append(CPI_tot_2 * sample.instructions)
        Ins_2.append(sample.instructions)
        prev_BW_used_2 = BW_used_2
        prev_CPI_tot_2 = CPI_tot_2

    return Cyc_2, Ins_2, BW_list, Rd_list, BW_list_baseline

def estimate_perf(cpi_target, app_profile: AppProfile, cpu_config_path: str, baseline_curves: Curves,
                  target_curves: Curves, display_warnings: bool = True) -> dict:
    """
    Goes trough the traces and calls the functions to calculate performance estimations, sweeping different values of Ins_ooo_percentage.

    Args:
        app_profile (AppProfile): directory containing the application profiling (Str)
        cpu_config (str): directory containing the CPU configuration file.
        baseline_curves (Curves): Curves class for the baseline memory system.
        target_curves (Curves): Curves class for the target memory system.
        display_warnings (bool): if True, warnings are displayed.

    Returns:
        dictionary containing the results of the performance estimation.
    """

    # We use nomenclature as introduced in the paper
    # Important note: in Cyc_tot, total reffers to Cyc_0+Cyc_LLC, not total cycles for the whole application
    # We use keyword "overall" to refer to numbers for the whole application (all samples)

    with open(cpu_config_path) as f:
        cpu_config = json.load(f)

    sweep_results = SweepResults()
    # print(f'{app_profile.name}')
    # perform sensitivity (sweep) analysis for Ins_ooo parameter: from minimum to maximum using 10% step
    for Ins_ooo_percentage in (0., .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.):
        Cyc_2, Ins_2, BW_list, Rd_list, BW_list_baseline= estimate_profiling_samples(app_profile, cpu_config, baseline_curves, target_curves, Ins_ooo_percentage, display_warnings)
        sweep_results.add_prediction(Ins_ooo_percentage, sum(Cyc_2), sum(Ins_2))

    # Final result is the average of sensitivity (sweep) analysis
    # Calculate mean, min and max predicted IPC for the whole benchmark on system 2 (target)
    sweep_results.aggregate_results()


    #add the function to plot the chart
    #baseline_bws_gbs, baseline_lats_cyc = get_bws_lats(app_profile, baseline_curves)
    # TODO add target bws and lats
    # TODO add baseline and target memory names in plot curves? (e.g. DDR4 and MCDRAM)
    #viz.plot_baseline_and_target_curves(baseline_curves, target_curves, bw_unit='GBps',
                                        #baseline_bws = baseline_bws_gbs, baseline_lats = baseline_lats_cyc,
                                        #lat_unit='cycles', gradient=True, filepath=args.plot_to_pdf)


    result = results.Results.init_empty_result()
    # Calculate performance (IPC) difference relative to the measured IPC on the baseline system
    # print(f'{round(app_profile.total_IPC, 2)} / {round(sweep_results.mean_IPC, 2)}')
    result['IPC.base'] = app_profile.total_IPC
    result['IPC.target'] = sweep_results.mean_IPC
    result['IPC.change.avg'] = (sweep_results.mean_IPC / app_profile.total_IPC - 1.) * 100.
    # Calculate error bars (distance from min/max IPC diff. rel. to measured IPC to average IPC diff. rel. to measured IPC)
    result['IPC.change.min'] = result['IPC.change.avg'] - 100. * (sweep_results.min_IPC / app_profile.total_IPC - 1.)
    result['IPC.change.max'] = 100. * (sweep_results.max_IPC / app_profile.total_IPC - 1.) - result['IPC.change.avg']
    result['CPI.base'] = app_profile.total_CPI
    result['CPI.target'] = sweep_results.mean_CPI
    result['CPI.change.avg'] = (sweep_results.mean_CPI / app_profile.total_CPI - 1.) * 100.
    result['CPI.change.min'] = result['CPI.change.avg'] - 100. * (sweep_results.min_CPI / app_profile.total_CPI - 1.)
    result['CPI.change.max'] = 100. * (sweep_results.max_CPI / app_profile.total_CPI - 1.) - result['CPI.change.avg']

    return result, BW_list, Rd_list

def custom_dir(p: str) -> str:
    # TODO is this necessary? Could we do this in a better way?
    if not os.path.exists(p):
        raise ValueError
    return p

def parse_arguments() -> argparse.Namespace:
    # TODO fix readme with correct info about arguments
    parser = argparse.ArgumentParser(description="Estimate system performance using two memory configurations.",
                                     epilog="All paths have to exist. For the details on the format of input files/directories, please check the documentation.")
    # required parameters
    # TODO improve help explanations
    parser.add_argument('app_profiling_base', type=custom_dir, help='Directory containing application profiling files.')
    #parser.add_argument('app_profiling_target', type=custom_dir, help='Directory containing application profiling files.')
    parser.add_argument('cpu_config', type=custom_dir, help='Directory containing CPU configuration file.')
    parser.add_argument('mem_base', type=custom_dir, help='Directory containing bandwith-latency dependencies for the baseline system.')
    parser.add_argument('mem_target', type=custom_dir, nargs='?', help='Optional: Directory containing bandwith-latency dependencies for the target system.')

    # optional parameters
    parser.add_argument('-w', '--ignore-warnings', action='store_true', help='Ignore warning messages.')
    parser.add_argument('-p', '--plot-to-pdf', metavar='FILE', type=str, help='Specify the location for storing the PDF plot.')

    return parser.parse_args()

def get_bws_lats(app_profile: AppProfile, cvs: Curves) -> tuple[list[Bandwidth], list[Latency]]:
    """
    Returns the bandwidths and latencies for the given application profiling and curves.

    Args:
        app_profile (AppProfile): directory containing the application profiling (Str)
        cvs (Curves): Curves class for the memory system.

    Returns:
        tuple containing the bandwidths (GB/s) and latencies (CPU cycles).
    """
    bws_mbs = []
    read_ratios = []
    for sample in app_profile:
        bws_mbs.append(sample.bw)
        read_ratios.append(sample.read_ratio)
    # Approximate read_ratios to the closest multiple of 2 for the curves
    read_ratios = [utils.approximate_read_ratio(rr) for rr in read_ratios]
    # Calculate latencies
    lats_cyc = [cvs.get_lat(rr, bw) for bw, rr in zip(bws_mbs, read_ratios)]
    bws_gbs = [bw.as_unit('GBps') for bw in bws_mbs]
    return bws_gbs, lats_cyc

def print_results(results: dict) -> None:
    """
    Prints the summary of the results of the performance estimation.

    Args:
        results (dict): dictionary containing the results of the performance estimation.

    Returns:
        None
    """
    for key, val in results.items():
        name = key.replace('.', ' ')
        if 'avg' in key:
            print(f'{name}: {round(val, 3)}%')
        else:
            print(f'{name}: {round(val, 3)}')

def run_single_curves(args: argparse.Namespace) -> None:
    """
    Allow visualization of the curves of a single memory system.

    Args:
        args (argparse.Namespace): command-line arguments.

    Returns:
        None
    """
    if not args.plot_to_pdf:
        raise ValueError('When indicating a single curves file, please specify the location for storing the PDF plot. '\
                         'This can be done with the -p option. '\
                         'If the intention was to compare two curves, please provide two curves files instead of one. '\
                         'See --help for more information.')
    display_warnings = not args.ignore_warnings
    baseline_curves = Curves(args.mem_base, display_warnings)
    # TODO this could be optimized by only reading the bandwidth values in the app profiling
    app_profile = AppProfile(args.app_profiling_base)
    # measured bandwidths and the corresponding latencies
    bws_gbs, lats_cyc = get_bws_lats(app_profile, baseline_curves)
    # viz.plot_curves(baseline_curves, bw_units='GB/s', lat_units='cycles',
    viz.plot_curves(baseline_curves, bw_units='GB/s', lat_units='cycles', bws=bws_gbs, lats=lats_cyc,
                    color='Blues', gradient=True, filepath=args.plot_to_pdf)

def run_baseline_and_target_curves(args: argparse.Namespace, benchPath, cpi_target, benchname) -> None:
    """
    Predict memory performance when changing memory system from baseline to target.
    Optionally, allow visualization of the curves of two memory systems and estimation of the performance difference.

    Args:
        args (argparse.Namespace): command-line arguments.

    Returns:
        None
    """
    app_profile = AppProfile(benchname, benchPath)
    display_warnings = not args.ignore_warnings
    baseline_curves = Curves(args.mem_base, display_warnings)
    target_curves = Curves(args.mem_target, display_warnings)
    results, predict_bws, predict_rd = estimate_perf(
        cpi_target,
        app_profile,
        args.cpu_config,
        baseline_curves,
        target_curves,
        display_warnings,

    )
    #print_results(results)
    baseline_bws_gbs, baseline_lats_cyc = get_bws_lats(app_profile, baseline_curves)
    # TODO add target bws and lats
    # TODO add baseline and target memory names in plot curves? (e.g. DDR4 and MCDRAM)
    read_ratios = [utils.approximate_read_ratio(rr) for rr in predict_rd]
    target_lats_cyc = [target_curves.get_lat(rr, bw) for bw, rr in zip(predict_bws, read_ratios)]
    target_bws_gbs = [bw.as_unit('GBps') for bw in predict_bws]
    viz.plot_baseline_and_target_curves(baseline_curves, target_curves, bw_unit='GBps',
                                        baseline_bws = baseline_bws_gbs, baseline_lats = baseline_lats_cyc, target_bws=target_bws_gbs,
                                        target_lats=target_lats_cyc, lat_unit='cycles', gradient=True, filepath=os.path.join(args.plot_to_pdf, benchname))
    #if args.plot_to_pdf:
        # measured bandwidths and the corresponding latencies
        #baseline_bws_gbs, baseline_lats_cyc = get_bws_lats(app_profile, baseline_curves)
        # TODO add target bws and lats
        # TODO add baseline and target memory names in plot curves? (e.g. DDR4 and MCDRAM)
        #viz.plot_baseline_and_target_curves(baseline_curves, target_curves, bw_unit='GBps',
                                            #baseline_bws = baseline_bws_gbs, baseline_lats = baseline_lats_cyc,
                                            #lat_unit='cycles', gradient=True, filepath=args.plot_to_pdf)
    return results

def main():
    # parse the command-line arguments

    args = parse_arguments()
    res = results.Results()

    IPC_est_err_list = []
    CPI_est_err_list = []
    # run with single or two curves
    cpi_target=[]
    cpi_base = utils.load_cpi(args.app_profiling_base)
    benchmarks = [d for d in os.listdir(args.app_profiling_base) if os.path.isdir(os.path.join(args.app_profiling_base, d))]
    if args.mem_target is None:
        run_single_curves(args)
    else:
        for bench in benchmarks:
            print(bench)
            benchPath = os.path.join(args.app_profiling_base, bench)
            result = run_baseline_and_target_curves(args, benchPath,cpi_target, bench)
            res.add_result(bench, result)

        #res.sort(sorter)
        res.print_results(args)
        filename = 'results_' + args.mem_base.split('/')[3].rstrip('/') + '_' + args.mem_target.split('/')[3].rstrip('/') + '.csv'
        #res.save_to_file(filename)
        
        res.plot("IPC", args.mem_base.split('/')[3].rstrip('/'), args.mem_target.split('/')[3].rstrip('/'), args)
        res.plot("CPI", args.mem_base.split('/')[3].rstrip('/'), args.mem_target.split('/')[3].rstrip('/'), args)
if __name__ == "__main__":
    main()
