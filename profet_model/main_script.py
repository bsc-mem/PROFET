#!/usr/bin/env python

################################################################################
# Copyright (c) 2019, Milan Radulovic
#                     Rommel Sanchez Verdejo
#                     Paul Carpenter
#                     Petar Radojkovic
#                     Bruce Jacob
#                     Eduard Ayguade
#                     Contact: milan.radulovic [at] bsc [dot] es
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

from __future__ import print_function
import sys
from os import path,listdir,mkdir
from math import sqrt,pow,log,exp,factorial,floor
import numpy as np
import operator
import matplotlib.pyplot as plt
import utilities as util
import model
import measured_results as meas_res

__version__ = "1.0"
__status__ = "Release"

def estimate_perf(platform, benchmark, traces, bwlats, mem_conf_names):
    """
    Goes trough the traces and calls the functions to calculate performance estimations.
    @params:
        platform       - Required : platform name (Str)
        benchmark      - Required : benchmark name (Str)
        traces         - Required : trace of measured cycles, instructions, LLC misses and bandwidth (Dictionary of lists of floats)
        bwlats         - Required : bandwidth-latency dependency of both mem. conf. (Dictionary of lists of floats)
        mem_conf_names - Required : names of the memory configurations, e.g. '800', '1600', 'ddr4', 'mcdram' etc. (List of str)

    """

    # define start and end timings
    if len(traces['timings']) == 1:
        start_time = 0.
        end_time = traces['timings'][0]
    else:
        start_time = traces['timings'][0]
        end_time = traces['timings'][1]

    performance_ratio_tmp = []
    power_ratio_tmp = []
    energy_ratio_tmp = []
    Cyc_tot_2 = []
    BW_used_2_list = []
    P_tot_2_list = []
    E_tot_2_list = []
    results = {'avg': 0., 'min': 0., 'max': 0., 'perf_est_err': 0.,
               'pwr_avg': 0., 'pwr_min': 0., 'pwr_max': 0., 'pwr_est_err': 0.,
               'en_avg': 0., 'en_min': 0., 'en_max': 0., 'en_est_err': 0.}

    prev_BW_used_2 = 0.

    # perform sensitivity (sweep) analysis for Ins_ooo parameter: from minimum to maximum using 10% step
    for Ins_ooo_percentage in (0., .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.):
        del Cyc_tot_2[:]
        del BW_used_2_list[:]
        del P_tot_2_list[:]
        del E_tot_2_list[:]


        n = 0
        if start_time != 0.:
            while traces['time'][n] < start_time:
                n = n + 1
        n_start = n

        while traces['time'][n] <= end_time:

            # calculate performance estimation
            CPI_tot_2, BW_used_2, status = model.calc_perf( platform,
                                                   bwlats['bw'][1],
                                                   bwlats['lat'][1],
                                                   traces['bw'][n],
                                                   traces['bw_ratio'][n],
                                                   traces['cycles'][n],
                                                   traces['llc_misses'][n],
                                                   traces['instructions'][n],
                                                   bwlats['bw'][0],
                                                   bwlats['lat'][0],
                                                   Ins_ooo_percentage
                                                 )

            if status == -1:
                # the result is not converging: it may happen in rare cases;
                if prev_BW_used_2 != 0:
                    BW_used_2 = prev_BW_used_2
                    CPI_tot_2 = prev_CPI_tot_2

            BW_used_2_list.append(BW_used_2)
            Cyc_tot_2.append(CPI_tot_2*traces['instructions'][n])
            prev_BW_used_2 = BW_used_2
            prev_CPI_tot_2 = CPI_tot_2

            if platform == 'snb':
                # calculate power estimation
                P_tot_2 = model.calc_pwr( traces['bw_r'][n],
                                            traces['bw_w'][n],
                                            traces['page_empty'][n],
                                            traces['page_miss'][n],
                                            traces['page_hit'][n],
                                            traces['powerdown'][n],
                                            traces['selfref'][n],
                                            traces['pwrs'][n],
                                            mem_conf_names,
                                            BW_used_2*traces['bw_ratio'][n],
                                            BW_used_2*(1-traces['bw_ratio'][n])
                                          )

                P_tot_2_list.append(P_tot_2)
                E_tot_2_list.append(P_tot_2/(traces['cycles'][n]/Cyc_tot_2[-1]))

            n += 1

        performance_ratio_tmp.append(sum(traces['cycles'][n_start:n])/sum(Cyc_tot_2))
        if platform == 'snb':
            energy_ratio_tmp.append(sum(E_tot_2_list))
            power_ratio_tmp.append((energy_ratio_tmp[-1]/sum(traces['pwrs'][n_start:n]))*performance_ratio_tmp[-1]*np.mean(traces['pwrs'][n_start:n]))

    # final result is the average of sensitivity (sweep) analysis
    results['avg'] = (np.mean(performance_ratio_tmp)-1.)*100.
    results['min'] = results['avg'] - ((min(performance_ratio_tmp)-1.)*100.)
    results['max'] = (max(performance_ratio_tmp)-1.)*100. - results['avg']

    if platform == 'snb':
        results['pwr_avg'] = (np.mean(power_ratio_tmp)/np.mean(traces['pwrs'][n_start:n])-1.)*100.
        results['pwr_min'] = 100.*(np.mean(power_ratio_tmp) - min(power_ratio_tmp))/np.mean(traces['pwrs'][n_start:n])
        results['pwr_max'] = (max(power_ratio_tmp) - np.mean(power_ratio_tmp))/np.mean(traces['pwrs'][n_start:n])*100.

        results['en_avg'] = (np.mean(energy_ratio_tmp)/sum(traces['pwrs'][n_start:n])-1.)*100. # alternative would be to sum pwr*T_sample, in our case T_sample is 1s
        results['en_min'] = (np.mean(energy_ratio_tmp) - min(energy_ratio_tmp))/sum(traces['pwrs'][n_start:n])*100.
        results['en_max'] = (max(energy_ratio_tmp) - np.mean(energy_ratio_tmp))/sum(traces['pwrs'][n_start:n])*100.

    # calculate the estimation error
    if platform == 'snb':
        measured_cpi = meas_res.cpi_snb
    else:
        measured_cpi = meas_res.cpi_knl

    # the error in % is calculated as absolute(predicted_value/measured_value-1)*100
    results['perf_est_err'] = abs( (results['avg']/100.+1.)/(measured_cpi[benchmark][mem_conf_names[0]]/measured_cpi[benchmark][mem_conf_names[1]]) - 1. )*100.
    if platform == 'snb':
        results['pwr_est_err'] = abs( (results['pwr_avg']/100.+1.)/(meas_res.pwr_snb[benchmark][mem_conf_names[1]]/meas_res.pwr_snb[benchmark][mem_conf_names[0]]) - 1. )*100.
        results['en_est_err']  = abs( (results['en_avg']/100.+1.)/ \
                                      ((meas_res.pwr_snb[benchmark][mem_conf_names[1]]/meas_res.pwr_snb[benchmark][mem_conf_names[0]])/(measured_cpi[benchmark][mem_conf_names[0]]/measured_cpi[benchmark][mem_conf_names[1]])) - 1. )*100.

    return results

def main(argv=None):

    import argparse

    global no_of_processes

    bw_trace_exists = True

    parser = argparse.ArgumentParser(description="Program estimates system performance, power and energy difference using two memory configurations.",
                                     epilog="All paths have to be existing ones.")
    # required parameters
    parser.add_argument('-traces_dir', required=True, help='Directory with input traces of all workloads.')
    parser.add_argument('-mem_confs', required=True, nargs='*', help='Directories of bandwith-latency dependencies.')
    parser.add_argument('-platform', required=True, help='Experimental platform: Sandy Bridge (snb) or Knights Landing (knl).')

    # check if all input arguments are valid
    args = parser.parse_args()

    if not(path.exists(args.traces_dir)):
        print('\n[ERR]: An existent path to trace files must be provided.\n')
        return 1

    for mem_conf in args.mem_confs:
        if not(path.exists(mem_conf)):
            print('\n[ERR]: An existent path to bandwidth-latency dependencies must be provided.\n')
            return 1

    if args.platform not in ['snb', 'knl']:
        print('\n[ERR]: Please choose a valid platform: Sandy Bridge (snb) or Knights Landing (knl).\n')
        return 1

    bwlats = {'bw':{},'lat':{}}
    perf_est_err_list = []
    pwr_est_err_list = []
    en_est_err_list = []
    mem_conf_names = []

    # extract the names of memory configurations
    for mem_conf in args.mem_confs:
        mem_conf_names.append(mem_conf.split('/')[-1])

    # load bandwidth-latency dependency curves
    util.load_bwlats(bwlats, args.mem_confs)

    if args.platform == 'snb':
        traces = {'timings':[],
                  'bw':[],
                  'bw_ratio':[],
                  'bw_r':[],
                  'bw_w':[],
                  'cycles':[],
                  'instructions':[],
                  'llc_misses':[],
                  'page_empty':[],
                  'page_miss':[],
                  'page_hit':[],
                  'powerdown':[],
                  'selfref':[],
                  'pwrs':[],
                  'time':[]
                 }
        files  = {'timings':[],
                  'bw':[],
                  'cycles':[],
                  'instructions':[],
                  'llc_misses':[],
                  'page_stats':[],
                  'pwr_stats':[],
                  'pwrs':[]
                 }
    else:
        traces = {'timings':[],
                  'bw':[],
                  'bw_ratio':[],
                  'bw_r':[],
                  'bw_w':[],
                  'cycles':[],
                  'instructions':[],
                  'llc_misses':[],
                  'time':[]
                 }
        files  = {'timings':[],
                  'bw':[],
                  'cycles':[],
                  'instructions':[],
                  'llc_misses':[]
                 }

    # list all the benchmarks and sort them in the appropriate order
    if args.platform == 'snb':
        benchmarks_list = sorted(listdir(args.traces_dir), key=util.getkey_snb)
        high_bw_workloads = 10
        measured_cpi = meas_res.cpi_snb
    else:
        benchmarks_list = sorted(listdir(args.traces_dir), key=util.getkey_knl)
        high_bw_workloads = 12
        measured_cpi = meas_res.cpi_knl


    print('\n-Estimation results:')
    print('           |            Performance estimation              ', end = '')
    if args.platform == 'snb':
        print('||               Power estimation                ', end = '')
        print('||               Energy estimation               ', end = '')
    print('\n benchmark |    avg   |   min  |   max  | measured |  error ', end = '')
    if args.platform == 'snb':
        print('||   avg   |   min  |   max  | measured |  error ', end = '')
        print('||    avg   |   min  |   max  | measured |  error ', end = '')
        print('\n' + 160*'.')
    else:
        print('\n' + 60*'.')

    # for each benchmark load the trace, estimate performance and print the results
    for benchmark in benchmarks_list:
        util.load_traces(args.platform, benchmark, args.traces_dir, files, traces)
        result = estimate_perf(args.platform, benchmark, traces, bwlats, mem_conf_names)
        measured_perf_rel = measured_cpi[benchmark][mem_conf_names[0]]/measured_cpi[benchmark][mem_conf_names[1]]
        if args.platform == 'snb':
            measured_pwr_rel  = meas_res.pwr_snb[benchmark][mem_conf_names[1]]/meas_res.pwr_snb[benchmark][mem_conf_names[0]]
            measured_en_rel   = measured_pwr_rel/measured_perf_rel
        print('{0:11}'.format(benchmark) + '|' +
              '{0:8.3f}'.format(result['avg']) + '% | ' +
              '{0:6.3f}'.format(result['min']) + ' | ' +
              '{0:6.3f}'.format(result['max']) + ' | ' +
              '{0:7.3f}'.format((measured_perf_rel-1.)*100.) + '% | ' +
              '{0:5.2f}'.format(result['perf_est_err']) + '%', end = ''
             )
        if args.platform == 'snb':
            print(' ||' +
                  '{0:7.3f}'.format(result['pwr_avg']) + '% |' +
                  '{0:7.3f}'.format(result['pwr_min']) + ' |' +
                  '{0:7.3f}'.format(result['pwr_max']) + ' |' +
                  '{0:7.3f}'.format((measured_pwr_rel-1.)*100.) + '%  | ' +
                  '{0:5.2f}'.format(result['pwr_est_err'])  + '% || '
                  '{0:7.3f}'.format(result['en_avg']) + '% | ' +
                  '{0:6.3f}'.format(result['en_min']) + ' | ' +
                  '{0:6.3f}'.format(result['en_max']) + ' | ' +
                  '{0:7.3f}'.format((measured_en_rel-1.)*100.) + '% | ' +
                  '{0:5.2f}'.format(result['en_est_err']) + '%', end = ''
                 )
        print("\n", end = '')
        perf_est_err_list.append(result['perf_est_err'])
        pwr_est_err_list.append(result['pwr_est_err'])
        en_est_err_list.append(result['en_est_err'])

    print('\n-Performance estimation error:')
    if args.platform == 'snb':
        print('  High-bw benchmarks:     ' + '{0:5.2f}'.format(np.mean(perf_est_err_list[:high_bw_workloads]+perf_est_err_list[-4:-2])) + '%')
        print('  Low-bw benchmarks:      ' + '{0:5.2f}'.format(np.mean(perf_est_err_list[high_bw_workloads:-4]+perf_est_err_list[-2:])) + '%')
        print('\n-Power estimation error:')
        print('  High-bw benchmarks:     ' + '{0:5.2f}'.format(np.mean(pwr_est_err_list[:high_bw_workloads]+pwr_est_err_list[-4:-2])) + '%')
        print('  Low-bw benchmarks:      ' + '{0:5.2f}'.format(np.mean(pwr_est_err_list[high_bw_workloads:-4]+pwr_est_err_list[-2:])) + '%')
        print('\n-Energy estimation error:')
        print('  High-bw benchmarks:     ' + '{0:5.2f}'.format(np.mean(en_est_err_list[:high_bw_workloads]+en_est_err_list[-4:-2])) + '%')
        print('  Low-bw benchmarks:      ' + '{0:5.2f}'.format(np.mean(en_est_err_list[high_bw_workloads:-4]+en_est_err_list[-2:])) + '%')
    else:
        print('  High-bw benchmarks:     ' + '{0:5.2f}'.format(np.mean(perf_est_err_list[:high_bw_workloads])) + '%')
        print('  Low-bw benchmarks:      ' + '{0:5.2f}'.format(np.mean(perf_est_err_list[high_bw_workloads:])) + '%')
    print("\n", end = '')

    return 0

if __name__ == "__main__":
    status = main()
    sys.exit(status)
