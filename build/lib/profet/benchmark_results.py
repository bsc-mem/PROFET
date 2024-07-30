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

import itertools
import pandas as pd
import matplotlib.pyplot as plt

class Results:
    data = {}
    __df = None
    __df_valid = False
    __result_groups = ['IPC', 'CPI'] # P - power, E - energy
    __result_stats = ['base', 'target', 'change.avg', 'change.min', 'change.max', 'change.measured', 'change.estimation_error']
    __pretty_keys = ['.'.join([g,s]) for g, s in itertools.product(__result_groups, __result_stats)]
    print(__pretty_keys)
    __sorting_order = []
    keys = __pretty_keys

    @classmethod
    def init_empty_result(cls):
        """ Return an empty dictionary that stores prediciton results for a single benchmark

        """
        return {k : 0 for k in cls.keys}

    def __init__(self):
        self.data['benchmark'] = []
        for key in self.keys:
            self.data[key] = []

    def add_result(self, benchmark, result):
        self.__df_valid = False
        self.data['benchmark'].append(benchmark)
        for key, val in result.items():
#            assert(key in keys, f'Key {key} not in list of supported keys:\n{keys}')
            self.data[key].append(val)

    def __update_df(self):
        if self.__df_valid:
            return
        print(self.data)
        print(self.keys)
        self.__df = pd.DataFrame(self.data, columns=['benchmark'] + self.keys)
        self.__df.columns = ['benchmark'] + self.__pretty_keys
        self.__df_valid = True


    def sort(self, sorter):
        self.__update_df()
        self.__df.sort_values(by='benchmark',
                key=lambda series: pd.Series(pd.Categorical(series, categories=sorter.get_order(), ordered=True)),
                inplace=True)

    def print_results(self, args):
        self.__update_df()
        formatters = {}
        for c in self.__pretty_keys:
            if 'avg' in c or 'measured' in c:
                formatters[c] = lambda x : '{:.3f}%'.format(x)
            else:
                formatters[c] = lambda x : '{:.3f}'.format(x)


        print('-Estimation results:')
        print(self.__df.to_string(columns=[c for c in self.__df.columns if (self.__df[c] != 0).any()],
                           col_space = 8, header=True, index=False, formatters=formatters))

    def print_summary(self):
        # TODO
        pass

    def save_to_file(self, filename):
        self.__update_df()
        self.__df.to_csv(filename)
        pass

    def plot(self, metric, baseline, target, args):
        filename = 'results_' + metric + '.pdf'
        self.__update_df()
        df = self.__df
        fig, ax = plt.subplots(1,1)
        plt.rcParams['font.size'] = 13
        plt.yticks(fontsize=13)
        ax.bar(x=df['benchmark'], height=df[f'{metric}.change.avg'], yerr=[df[f'{metric}.change.min'].tolist()] + [df[f'{metric}.change.max'].tolist()], capsize=3,
                width=0.5, color='#cccccc', label=f'{metric} change estimated')
        ax.legend()
        ax.set_ylabel(f'{metric} difference vs. the baseline [%]', fontsize=13)
        #ax.set_title(f'Profet estimation results from {baseline} to {target}')
        if (df[f'{metric}.change.avg'].mean() > 0):
            bench_label_pos_args = {'top': False, 'labeltop': False, 'bottom': True, 'labelbottom': True}
        else:
            bench_label_pos_args = {'top': True, 'labeltop': True, 'bottom': False, 'labelbottom': False}
        ax.tick_params(axis='x', rotation=90, **bench_label_pos_args)
        plt.xticks(fontsize=13)
        ax.axhline(y=0, color='black', linewidth=0.5)
        fig.set_size_inches([12.2,6.86])
        fig.tight_layout()
        fig.savefig(filename)
        plt.close()
        pass