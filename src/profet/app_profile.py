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

import os
import numpy as np

from .metrics import Bandwidth


class Sample:
    """
    Sample corresponding to a single time point in the application profile.
    """
    
    def __init__(self, time):
        self.time = time
        self.bw_r = None
        self.bw_w = None
        self.cycles = None
        self.instructions = None
        self.llc_misses = None
        self.page_empty = None
        self.page_miss = None
        self.page_hit = None
        self.selfref = None
        self.bw = None
        self.read_ratio = None

    def get_time(self):
        return self.time

    def check_set_time(self, time):
        if self._time is None:
            self._time = time
        elif not self._time == time:
            raise ValueError

    def set_events(self, trace_type, event_values):
        setter_method = getattr(self, 'set_' + trace_type)
        assert(setter_method is not None)
        setter_method(event_values)

    def set_bw(self, vals):
        self.bw_r = vals[0]
        self.bw_w = vals[1]
        self.bw = Bandwidth(self.bw_r + self.bw_w, 'MBps')
        try:
            self.read_ratio = self.bw_r / self.bw.value
        except:
            self.read_ratio = 1
            print(f'RW ratio cannot be calculated. bw_r = {self.bw_r}, '
                  f'bw_w = {self.bw_w}')

    def set_cycles(self, vals):
        self.cycles = vals[0]

    def set_instructions(self, vals):
        self.instructions = vals[0]

    def set_llc_misses(self, vals):
        self.llc_misses = vals[0]

    def set_page_stats(self, vals):
        self.page_empty = vals[0]
        self.page_miss = vals[1]
        self.page_hit = vals[2]

    def __str__(self):
        return (f'time:{self.time} bw:{self.bw.value} cyc:{self.cycles} '
                f'ins:{self.instructions} llcmiss:{self.llc_misses}')

    def __repr__(self):
        return self.__str__()


class CounterParser:
    """
    Parser for the counters in the traces.
    """
    @staticmethod
    def parse_raw_line(raw_line):
        tokens = raw_line.rstrip('\n').split(',')
        # If a line starts with a digit, consider that it contains counter data
        # Otherwise, the line is considered to be a comment and is ignored
        # Note: this means a line starting with a negative number is not valid
        if len(tokens[0]) > 0 and tokens[0][0].isdigit():
            return [float(t) for t in tokens]
        else:
            return None

    @staticmethod
    def parse_time(trace_type, tokens):
        ttypes = ['bw', 'cycles', 'instructions', 'llc_misses', 'page_stats', 'pwr_stats']
        if trace_type in ttypes:
            return tokens[len(tokens) - 1]
        else:
            return None

    @staticmethod
    def parse(trace_type, tokens):
        parse_method = getattr(CounterParser, '_parse_' + trace_type)
        return parse_method(tokens)

    @staticmethod
    def _parse_bw(tokens):
        count = len(tokens)
        assert(count >= 3)
        return ([sum(tokens[0 : (count - 1) // 2]),
                 sum(tokens[(count - 1) // 2 : count - 1])])

    @staticmethod
    def _parse_cycles(tokens):
        count = len(tokens)
        assert(count > 0)
        return [np.mean(tokens[0 : count - 1])]

    @staticmethod
    def _parse_instructions(tokens):
        count = len(tokens)
        assert(count > 0)
        return [np.mean(tokens[0 : count - 1])]

    @staticmethod
    def _parse_llc_misses(tokens):
        count = len(tokens)
        assert(count > 0)
        return [np.mean(tokens[0 : count - 1])]

    @staticmethod
    def _parse_page_stats(tokens):
        count = len(tokens)
        #TODO: put a count check here
        page_empty = np.mean(tokens[0 : (count - 1) // 3])
        page_miss = np.mean(tokens[(count - 1) // 3 : 2 * (count - 1) // 3])
        page_hit = max(0, np.mean(tokens[2 * (count - 1) // 3 : count - 1]))
        return [page_empty, page_miss, page_hit]


class AppProfile:
    """
    Application profile class for processing profiling traces.
    """

    _performance_trace_types = ['bw', 'cycles', 'instructions', 'llc_misses']

    def __init__(self, app_profile_path, name=""):
        self.name = name
        self._time_parsed = False
        self._samples = {}
        self._complete_traces = {k : False for k in self._performance_trace_types}
        self._trace_dir = app_profile_path
        self._load_traces()
        self._load_time_limits()
        self._even_metrics()
        self._compute_derived_metrics()

    def completed_event_type(self, event_type):
        self._complete_traces[event_type] = True

    def sample_count(self):
        return len(self._samples)

    def __iter__(self):
        return SampleIterator(self)

    @staticmethod
    def _trace_has_time(trace_type):
        ttypes = ['bw', 'cycles', 'instructions', 'llc_misses', 'page_stats', 'pwr_stats']
        return trace_type in ttypes

    def _load_traces(self):
        # Load traces from files, parse the events and store them into samples
        for trace_type in self._performance_trace_types:
            """
            Some traces have slightly mismatching times among themselves due
            to negligible noise. In the original code, this was ignored.
            Here we take similar approach:
                1. Take time from one trace.
                2. Match samples from other traces by order in file.
            """
            try:
                fname = os.path.join(self._trace_dir, trace_type + '.csv')
                with open(fname, 'r') as f:
                    if not self._time_parsed:
                        if not AppProfile._trace_has_time(trace_type):
                            print('[ERROR] Reading trace without the times before '
                                  'reading times from other trace.')
                            print('[-----] This is a bug in the Profet code.')
                            exit()
                        else:
                            for raw_line in f:
                                tokens = CounterParser.parse_raw_line(raw_line)
                                if tokens is not None:
                                    time = CounterParser.parse_time(trace_type, tokens)
                                    parsed_event_values = CounterParser.parse(trace_type, tokens)
                                    assert(time not in self._samples)
                                    self._samples[time] = Sample(time)
                                    self._samples[time].set_events(trace_type, parsed_event_values)
                            self._time_parsed = True
                    else:
                        curr_sample_idx = 0
                        times = list(self._samples.keys())
                        for raw_line in f:
                            tokens = CounterParser.parse_raw_line(raw_line)
                            if tokens is not None and curr_sample_idx < len(times):
                                parsed_event_values = CounterParser.parse(trace_type, tokens)
                                self._samples[times[curr_sample_idx]].set_events(trace_type, parsed_event_values)
                                curr_sample_idx += 1
                    self.completed_event_type(trace_type)
            except FileNotFoundError:
                #print(f'no {trace_type}')
                pass

    def _load_time_limits(self):
        with open(os.path.join(self._trace_dir, 'timings.csv'), 'r') as f:
            for raw_line in f:
                tokens = CounterParser.parse_raw_line(raw_line)
                if tokens is not None:
                    if len(tokens) == 2:
                        self._start_time = tokens[0]
                        self._end_time = tokens[1]
                    elif len(tokens) == 1:
                        self._start_time = 0
                        self._end_time = tokens[0]
                    else:
                        print(f'ERROR: bad file format for {self._name} and timings.csv')
                        exit()
                    # There is only one valid line in this file,
                    # so we quit the loop after processing it
                    break
        # Sometimes end_time in traces is after the application finishes
        # Consequently, the end_time can be after the last recorded time in the trace
        # If that happens, we correct the end_time
        last_recorded_time = sorted(list(self._samples.keys()))[-1]
        if (last_recorded_time < self._end_time):
            print(f'Correcting end_time: {self._end_time} -> {last_recorded_time}')
            self._end_time = last_recorded_time

    def _even_metrics(self):
        keys = list(self._samples.keys())
        for key in keys:
            if self._samples[key].cycles is None or self._samples[key].bw is None:
                del self._samples[key]

    def _compute_derived_metrics(self):
        self.total_cycles = sum([s.cycles for s in self])
        self.total_instructions = sum([s.instructions for s in self])
        self.total_IPC = self.total_instructions / self.total_cycles
        self.total_CPI = self.total_cycles / self.total_instructions


class SampleIterator:
    """Iterator class for the Sample class"""

    def __init__(self, app_profile):
        self._app_profile = app_profile
        self._start_time = self._app_profile._start_time
        self._end_time = self._app_profile._end_time
        self._times = sorted(self._app_profile._samples.keys())
        # index variable to keep track
        self._index = 0
        while self._times[self._index] < self._start_time:
            self._index += 1

    def __next__(self):
        """'Returns the next value from school object's lists"""
        if self._index < len(self._times) and self._times[self._index] <= self._end_time:
            result = self._app_profile._samples[self._times[self._index]]
            self._index += 1
            return result
        else:
            # Iteration ends
            raise StopIteration

