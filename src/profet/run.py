#!/usr/bin/env python3

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

import argparse
import os
import sys
import warnings
import json
import pandas as pd

# Ensure profet modules can be imported
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from profet import visualization as viz
from profet import estimate_performance
from profet.metrics import Bandwidth, Latency, Frequency
from profet.curves import Curves, OvershootError
from profet.app_profile import AppProfile


def latencies_cycles_warning() -> None:
    warn = ('DRAM configuration file not provided, plotting latencies in cycles '
            'instead of ns.')
    warnings.warn(warn)


def custom_dir(p: str) -> str:
    if not os.path.exists(p):
        raise Exception(f'The specified "{p}" directory does not exist.')
    return p


def custom_json(p: str) -> str:
    if not os.path.exists(p):
        raise Exception(f'The specified "{p}" configuration file does not exist.')
    if not p.endswith('.json'):
        raise Exception(f'The specified "{p}" configuration file must be a JSON file.')
    return p


def parse_arguments() -> argparse.Namespace:
    descr = 'Estimate system performance using two memory configurations.'
    epi = ('All paths have to exist. For the details on the format of input '
          'files/directories, please check the documentation.')
    parser = argparse.ArgumentParser(description=descr, epilog=epi)
    
    # Help messages
    help_app = 'Directory containing application profiling files.'
    help_config = 'System configuration file.'
    help_mem = 'Directory containing bandwith-latency dependencies for the baseline system.'
    help_target = ('Optional: Directory containing bandwith-latency '
                   'dependencies for the target system.')
    help_bench = ('Optional: Application profiling directory expected to '
                  'contain subdirectories with the benchmarking app profilings.')
    help_plt = 'Optional: Specify the location for storing the PDF plot.'
    help_iw = 'Optional: Ignore warning messages.'

    # Required parameters
    parser.add_argument('-a', '--app-profiling', type=custom_dir, help=help_app, required=True)
    parser.add_argument('-c', '--config', type=custom_json, help=help_config, required=True)
    parser.add_argument('--mem-base', type=custom_dir, help=help_mem, required=True)

    # Optional parameters
    parser.add_argument('--mem-target', type=custom_dir, help=help_target)
    parser.add_argument('-b', '--benchmarking', action='store_true', help=help_bench)
    parser.add_argument('-p', '--plot-to-pdf', metavar='FILE', type=str, help=help_plt)
    parser.add_argument('-w', '--ignore-warnings', action='store_true', help=help_iw)

    return parser.parse_args()


def read_config(config_path: str) -> dict:
    """
    Returns the configuration.

    Args:
        config_path (str): path to the configuration file.

    Returns:
        Dictionary containing the configuration.
    """
    if not config_path.endswith('.json'):
        raise Exception(f'The specified "{config_path}" '
                        'configuration file must be a JSON file.')
    with open(config_path) as f:
        return json.load(f)


def has_dram_freq(config) -> bool:
    """
    Returns whether the configuration data has the DRAM frequency set.

    Args:
        config (dict): configuration file.

    Returns:
        Boolean
    """
    if not config['DRAM'] or not config['DRAM']['Freq_MHz']:
        return False
    is_int = isinstance(config['DRAM']['Freq_MHz'], int)
    is_float = isinstance(config['DRAM']['Freq_MHz'], float)
    if not is_int and not is_float:
        raise Exception(f"The given DRAM frequency of {config['DRAM']['Freq_MHz']} "
                        "MHz is not in a correct format.")
    return True


def get_dram_freq(config: dict) -> Frequency:
    """
    Returns the DRAM frequency from the given configuration.

    Args:
        config (dict): configuration.

    Returns:
        Frequency object with the DRAM frequency.
    """
    return Frequency(config['DRAM']['Freq_MHz'], 'MHz')


def get_bws_lats(
    bws: list[Bandwidth],
    read_ratios: list[float],
    cvs: Curves
) -> tuple[list[Bandwidth], list[Latency]]:
    """
    Returns the bandwidths and latencies for the given application
    profiling and curves.

    Args:
        bws (list[Bandwidth]): list of measured bandwidths.
        read_ratios (list[float]): list of read ratios.
        cvs (Curves): Curves class for the memory system.

    Returns:
        tuple containing the bandwidths (GB/s) and latencies (CPU cycles).
    """
    # Calculate latencies
    lats_cyc = []
    bws_gbs = []
    for bw, rr in zip(bws, read_ratios):
        try:
            lats_cyc.append(cvs.get_lat(rr, bw))
            bws_gbs.append(bw.as_unit('GBps'))
        except OvershootError:
            pass
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
        if key != 'Target.BWs':
            name = key.replace('.', ' ')
            if 'avg' in key:
                print(f'{name}: {round(val, 3)}%')
            else:
                print(f'{name}: {round(val, 3)}')


def run_single_curves(
    mem_base_path: str,
    app_profiling_path: AppProfile,
    config: dict,
    plot_to_pdf_path: str = '',
    ignore_warnings: bool = False
) -> None:
    """
    Allow visualization of the curves of a single memory system.

    Args:
        mem_base_path (str): path to the base memory curves.
        app_profiling_path (AppProfile): path to application profiling files.
        config (dict): configuration data.
        plot_to_pdf_path(str, optional): path to store the pdf.
        ignore_warnings(bool, optional): whether to show warnings.

    Returns:
        None
    """
    if not plot_to_pdf_path:
        raise ValueError('When indicating a single curves file, please specify '
                         'the location for storing the PDF plot. '
                         'This can be done with the -p option. '
                         'If the intention was to compare two curves, please '
                         'provide two curves files instead of one. '
                         'See --help for more information.')
    display_warnings = not ignore_warnings
    baseline_curves = Curves(mem_base_path, display_warnings)
    # TODO could be optimized by only reading the bw values in the app profiling
    app_profile = AppProfile(app_profiling_path)
    # Measured bandwidths and the corresponding latencies
    bws_mbs = []
    read_ratios = []
    for sample in app_profile:
        bws_mbs.append(sample.bw)
        read_ratios.append(sample.read_ratio)
    bws_gbs, lats_cyc = get_bws_lats(bws_mbs, read_ratios, baseline_curves)
    # viz.plot_curves(baseline_curves, bw_units='GB/s', lat_units='cycles',
    if has_dram_freq(config):
        freq = get_dram_freq(config)
        lat_unit = 'ns'
    else:
        freq = None
        lat_unit = 'cycles'
    viz.plot_curves(baseline_curves, bw_unit='GBps', lat_unit=lat_unit,
                    bws=bws_gbs, lats=lats_cyc, freq=freq, color='Blues',
                    gradient=True, filepath=plot_to_pdf_path)


def run_baseline_and_target_curves(
    mem_base_path: str,
    mem_target_path: str,
    app_profiling_path: AppProfile,
    config: dict,
    benchmark_name: str = '',
    benchmarking: bool = False,
    plot_to_pdf_path: str = '',
    ignore_warnings: bool = False
) -> dict:
    """
    Predict memory performance when changing memory system from baseline to target.
    Optionally, allow visualization of the curves of two memory systems and
    estimation of the performance difference.

    Args:
        mem_base_path (str): path to the base memory curves.
        mem_target_path (str): path to the target memory curves.
        app_profiling_path (AppProfile): path to application profiling files.
        config (dict): configuration data.
        benchmark_name (str): name of the benchmark.
        benchmarking (bool, optional): whether we are benchmarking.
        plot_to_pdf_path(str, optional): path to store the pdf.
        ignore_warnings(bool, optional): whether to show warnings.

    Returns:
        Results dictionary
    """
    if benchmark_name:
        bench_path = os.path.join(app_profiling_path, benchmark_name)
        app_profile = AppProfile(bench_path, benchmark_name)
    else:
        app_profile = AppProfile(app_profiling_path, benchmark_name)
    display_warnings = not ignore_warnings
    baseline_curves = Curves(mem_base_path, display_warnings)
    target_curves = Curves(mem_target_path, display_warnings)
    results = estimate_performance(
        app_profile,
        config['CPU'],
        baseline_curves,
        target_curves,
        display_warnings
    )
    print_results(results)

    if plot_to_pdf_path and not benchmarking:
        is_dram_freq_set = has_dram_freq(config)
        if not is_dram_freq_set and display_warnings:
            latencies_cycles_warning()
            
        # Baseline: measured bandwidths and the corresponding latencies
        baseline_bws_mbs = []
        read_ratios = []
        for sample in app_profile:
            baseline_bws_mbs.append(sample.bw)
            read_ratios.append(sample.read_ratio)
        baseline_bws_gbs, baseline_lats = get_bws_lats(baseline_bws_mbs,
                                                       read_ratios,
                                                       baseline_curves)

        # Target: predicted bandwidths and the corresponding latencies
        target_bws_gbs, target_lats = get_bws_lats(results['Target.BWs'],
                                                   read_ratios,
                                                   target_curves)
        if is_dram_freq_set:
            freq = get_dram_freq(config)
            lat_unit = 'ns'
        else:
            freq = None
            lat_unit = 'cycles'

        # TODO add baseline and target mem. names in plot curves? (e.g. DDR4 or MCDRAM)
        viz.plot_baseline_and_target_curves(baseline_curves,
                                            target_curves,
                                            bw_unit='GBps',
                                            lat_unit=lat_unit,
                                            baseline_bws=baseline_bws_gbs,
                                            baseline_lats=baseline_lats,
                                            freq=freq,
                                            target_bws=target_bws_gbs,
                                            target_lats=target_lats,
                                            gradient=True,
                                            filepath=plot_to_pdf_path)
    return results


def main():
    # Parse the command-line arguments
    args = parse_arguments()

    if args.benchmarking and args.mem_target is None:
        raise ValueError('When benchmarking, please specify the target memory '
                         'system. This can be done with the --mem-target option. '
                         'See --help for more information.')
    
    # Read configuration file
    config = read_config(args.config)

    # Run with single or two curves
    if args.mem_target is None:
        # No target memory specified, just run as single curves
        run_single_curves(args.mem_base, args.app_profiling, config,
                          args.plot_to_pdf, args.ignore_warnings)
    elif args.benchmarking:
        benchmarks = [d for d in os.listdir(args.app_profiling)
                      if os.path.isdir(os.path.join(args.app_profiling, d))]

        if len(benchmarks) == 0:
            raise ValueError('When benchmarking, the application profiling '
                             'directory must contain subdirectories with '
                             'the benchmarking application profilings. '
                             'See --help for more information.')

        all_results = {}
        for bench_name in benchmarks:
            print(bench_name)
            print('---------------------')
            results = run_baseline_and_target_curves(args.mem_base,
                                                     args.mem_target,
                                                     args.app_profiling,
                                                     config,
                                                     bench_name,
                                                     args.benchmarking,
                                                     args.plot_to_pdf,
                                                     args.ignore_warnings)
            all_results[bench_name] = results
            print()
        if args.plot_to_pdf:
            all_results_df = pd.DataFrame(all_results).T.\
                                reset_index().\
                                rename(columns={'index': 'benchmark'})
            viz.plot_benchmark_results(all_results_df, 'IPC', args.plot_to_pdf)
            viz.plot_benchmark_results(all_results_df, 'CPI', args.plot_to_pdf)
    else:
        benchmark_name = ''
        run_baseline_and_target_curves(args.mem_base,
                                       args.mem_target,
                                       args.app_profiling,
                                       config,
                                       benchmark_name,
                                       args.benchmarking,
                                       args.plot_to_pdf,
                                       args.ignore_warnings)


if __name__ == "__main__":
    main()
