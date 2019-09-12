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
import numpy as np

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Predefined benchmarks order, sorted by memory bandwidth
predef_list_spec_snb = ['libquantum', 'bwaves', 'lbm', 'milc', 'soplex', 'GemsFDTD', 'leslie3d',
                        'mcf', 'sphinx3', 'wrf', 'omnetpp', 'zeusmp', 'cactusADM', 'astar',
                        'gcc', 'dealII', 'bzip2', 'gobmk', 'xalancbmk', 'sjeng', 'hmmer', 'tonto',
                        'gromacs', 'h264ref', 'calculix', 'namd', 'perlbench', 'gamess', 'povray', 'QE_1', 'QE_2', 'ALYA_1', 'ALYA_2', 'GROMACS_1', 'GROMACS_2', 'NAMD_1', 'NAMD_2', 'QE', 'ALYA', 'GROMACS', 'NAMD']

predef_list_spec_knl = ['sphinx3', 'leslie3d', 'libquantum', 'lbm', 'omnetpp', 'soplex', 'GemsFDTD',
                        'milc', 'cactusADM', 'gcc', 'astar', 'hmmer', 'zeusmp', 'xalancbmk', 'bwaves',
                        'wrf', 'dealII', 'h264ref', 'bzip2', 'mcf', 'gobmk', 'gromacs', 'sjeng',
                        'perlbench', 'tonto', 'namd', 'calculix', 'gamess', 'povray']

def getkey_snb(item):
    return predef_list_spec_snb.index(item)

def getkey_knl(item):
    return predef_list_spec_knl.index(item)

def eprint(*args, **kwargs):
    """
    Prints to stderr output.

    (Taken from: https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python)
    """
    print(*args, file=sys.stderr, **kwargs)

def load_bwlats(bwlats, mem_confs):
    """
    Loads bandwidth-latency dependency from the files containing measurements.
    @params:
     bwlats    - Required : array of measured bandwidths and latencies for bw-lat dep. (Lists of floats)
     mem_confs - Required : names of the memory configurations, e.g. '800', '1600', 'ddr4', 'mcdram' etc. (List of str)

    """

    bwlats['bw'] = [[] for i in range(2)]
    bwlats['lat'] = [[] for i in range(2)]

    for i in range(50,102,2):
        file_bwlat_1  = mem_confs[0] + '/bwlat_' + str(i) + '.txt'
        file_bwlat_2  = mem_confs[1] + '/bwlat_' + str(i) + '.txt'

        bwlats['bw'][0].append([])
        bwlats['lat'][0].append([])
        for line in reversed(open(file_bwlat_1).readlines()):
            tmp = line.split()
            if tmp == [] or '#' in tmp[0] or '\n' in tmp[0]:
                continue
            else:
                bwlats['bw'][0][(i-50)/2].append(float(tmp[0]))
                bwlats['lat'][0][(i-50)/2].append(float(tmp[1]))

        bwlats['bw'][1].append([])
        bwlats['lat'][1].append([])
        for line in reversed(open(file_bwlat_2).readlines()):
            tmp = line.split()
            if tmp == [] or '#' in tmp[0] or '\n' in tmp[0]:
                continue
            else:
                bwlats['bw'][1][(i-50)/2].append(float(tmp[0]))
                bwlats['lat'][1][(i-50)/2].append(float(tmp[1]))

def load_traces(platform, benchmark, traces_dir, files, traces):
    """
    Loads traces for all measured events from benchmark directory.
    @params:
     platform   - Required : platform name (Str)
     benchmark  - Required : benchmark name (Str)
     traces_dir - Required : directory with traces of measured cycles, instructions, LLC misses and bandwidth (Str)
     files      - Required : list with file names containing the traces for specific events. (List of str)
     traces     - Required : target structure that will contain traces for benchmark (Dictionary of lists of floats)

    """

    raw_output = []
    time_parsed = False

    # empty the traces dictionary
    for event in traces:
        del traces[event][:]

    for event in sorted(files):
        del raw_output[:]

        with open(traces_dir + '/' + benchmark + '/' + event + '.csv') as f:
            raw_output = f.readlines()

        for lnum in range(len(raw_output)):
            counter_values = raw_output[lnum].split(',')
            if counter_values == [] or '#' in counter_values[0] or (len(counter_values[0]) == 1 and '\n' in counter_values[0]):
                continue
            else:
                counter_values = map(float, counter_values)

            # extract bandwidth measurements
            if event == 'bw':
                read = sum(counter_values[ 0 : (( len(counter_values) - 1 ) / 2) ])
                write = sum(counter_values[ (( len(counter_values) - 1 ) / 2) : ( len(counter_values) - 1 ) ])
                traces['bw_r'].append(read)
                traces['bw_w'].append(write)
                traces['bw'].append(read + write)
                traces['bw_ratio'].append(read/(read+write))
            elif event == 'pwrs':
                traces[event].append(float(counter_values[0]))
            elif event == 'page_stats':
                traces['page_empty'].append(np.mean(counter_values[0 : (( len(counter_values) - 1 ) / 3)]))
                traces['page_miss'].append(np.mean(counter_values[(( len(counter_values) - 1 ) / 3) : 2*( len(counter_values) - 1 )/3]))
                if np.mean(counter_values[(2*( len(counter_values) - 1 ) / 3):( len(counter_values) - 1 )]) < 0:
                    traces['page_hit'].append(0.0)
                else:
                    traces['page_hit'].append(np.mean(counter_values[(2*( len(counter_values) - 1 ) / 3):( len(counter_values) - 1 )]))
            elif event == 'pwr_stats':
              traces['powerdown'].append(np.mean(counter_values[0 : (( len(counter_values) - 1 ) / 2)]))
              traces['selfref'].append(np.mean(counter_values[(( len(counter_values) - 1 ) / 2) : (len(counter_values) - 1 )]))
            else:
                # extract time measurements and benchmark runtime
                if len(counter_values) == 2:
                    traces[event].append(float(counter_values[0]))
                    traces[event].append(float(counter_values[1]))
                elif len(counter_values) == 1:
                    traces[event].append(float(counter_values[0]))
                else:
                    traces[event].append(np.mean(counter_values[0:( len(counter_values) - 1 )]))
                    if time_parsed == False:
                        traces['time'].append(counter_values[-1])

        if len(traces['time']) > 1:
        # since every event trace file has time, we extract it first time only
            time_parsed = True
