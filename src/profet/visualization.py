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
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd

from .curves import Curves
from .metrics import Bandwidth, Latency, Frequency


def get_cmap(
    color: str,
    read_ratio: float,
    read_ratios: list[float] = None
) -> matplotlib.colors.LinearSegmentedColormap:
    """
    Retrieve a pyplot color map for a given read ratio.

    Args:
        color (str): color palette to use (e.g. Reds, Blues, Greens, etc.).
            You can find them here:
            https://matplotlib.org/stable/tutorials/colors/colormaps.html.
        read_ratio (float): read ratio of the curve.
        read_ratios (list[float], optional): list of read ratios of the
            curves for plotting with a color gradient. Defaults to None.

    Returns:
        matplotlib.colors.LinearSegmentedColormap: color map for the
            given read ratio.
    """
    cmap = matplotlib.cm.get_cmap(color)

    if read_ratios is None:
        c = 0.8
    else:
        min_val = 0.2
        max_val = 1
        n_curves = len(read_ratios)
        # Find the color distance between each curve considering the number
        # of curves we want to plot
        dist = (max_val - min_val) / n_curves
        # Position of the curve in the set of distances
        rw_pos = n_curves - np.where(np.array(read_ratios) == read_ratio)[0][0]
        c = (n_curves - rw_pos) * dist + min_val

    return cmap(c)


def set_legend_curves(
    ax: matplotlib.axes.Axes,
    title: str,
    color: str,
    read_ratios: list[float] = None
) -> None:
    """
    Set the legend for the curves plot.

    Args:
        ax (matplotlib.axes.Axes): axes of the plot.
        title (str): title of the legend.
        color (str): color palette to use (e.g. Reds, Blues, Greens, etc.).
            You can find them here:
            https://matplotlib.org/stable/tutorials/colors/colormaps.html
        read_ratios (list[float], optional): list of read ratios of the
            curves for plotting with a color gradient. Defaults to None.

    Returns:
        None.
    """
    # lines for read-ratio of 50% and 100%
    lines = [
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(color, 50, read_ratios),
                                lw=4, label='Line'),
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(color, 100, read_ratios),
                                lw=4, label='Line'),
    ]
    leg = ax.legend(title=title, handles=lines, labels=['Rd:Wr 50:50', 'Rd:Wr 100:0'],
                    ncol=3, title_fontsize=16, fontsize=16)
    ax.add_artist(leg)


def set_legend_baseline_and_target_curves(
    ax: matplotlib.axes.Axes,
    baseline_read_ratios: list[float],
    baseline_color: str,
    baseline_name: str,
    target_read_ratios,
    target_color: str,
    target_name: str
) -> None:
    lines = [
        # invisible handle before the baseline system
        matplotlib.patches.Rectangle((0,0), 1, 1, fill=False,
                                     edgecolor='none', visible=False),
        # invisible handle before the target system
        matplotlib.patches.Rectangle((0,0), 1, 1, fill=False,
                                     edgecolor='none', visible=False),
        # read-ratio line of 50% for the baseline system
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(baseline_color, 0.5, baseline_read_ratios),
                                lw=4, label='Line'),
        # read-ratio line of 50% for the target system
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(target_color, 0.5, target_read_ratios),
                                lw=4, label='Line'),
        # read-ratio line of 100% for the baseline system
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(baseline_color, 1, baseline_read_ratios),
                                lw=4, label='Line'),
        # read-ratio line of 100% for the target system
        matplotlib.lines.Line2D([0], [0],
                                color=get_cmap(target_color, 1, target_read_ratios),
                                lw=4, label='Line'),
    ]
    labels = [f'{baseline_name}:', f'{target_name}:', 'Rd:Wr 50:50',
              'Rd:Wr 50:50', 'Rd:Wr 100:0', 'Rd:Wr 100:0']
    leg = ax.legend(handles=lines, labels=labels, ncol=3,
                    title_fontsize=16, fontsize=16)
    ax.add_artist(leg)


def set_curves_figure(
    ax: matplotlib.axes.Axes,
    cvs: Curves,
    bw_unit: str,
    lat_unit: str,
    freq: Frequency = None,
    color: str = 'Reds',
    gradient: bool = True,
    legend_title = ''
) -> None:
    """
    Set the curves plot figure to the given axes.

    Args:
        cvs (Curves): Curves object to plot.
        bw_unit (str): units of bandwidth to plot.
        lat_unit (str): units of latency to plot.
        color (str): color palette to use (e.g. Reds, Blues, Greens, etc.).
            You can find them here:
            https://matplotlib.org/stable/tutorials/colors/colormaps.html
        gradient (bool): if True, the color of the curves will change
            depending on the read ratio.
        legend_title (str): title of the legend.

    Returns:
        None.
    """

    # # Find bandwidth and latency max values to automatically set the limits
    # max_bw_dram = int(config['DRAM_MAX_CHANNELS'])*8*int(config['DRAM_FREQ']) / 1000 #in GB/s
    # Set the font size of the x-axis ticks
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.set_xlabel(f'Used memory bandwidth [{bw_unit}]', fontsize=17)
    ax.set_ylabel(f'Memory access latency [{lat_unit}]', fontsize=17)
    # Get experiment parameters
    # mem_type = config['MEM_TYPE'].replace("\"", "")
    # # Add plot details
    # plot_limit_line(ax, max_bw_dram, config)
    cvs_dict = cvs.get_curves_bws_lats(bw_unit, lat_unit, freq=freq)
    read_ratios = sorted(list(cvs_dict.keys())) if gradient else None

    if legend_title:
        set_legend_curves(ax, legend_title, color, read_ratios)

    # Plot curves
    for read_ratio in read_ratios:
        vals = cvs_dict[read_ratio]
        bws, lats = zip(*vals)
        # Take into account that bws and lats are Bandwidth and Latency objects
        bws_vals = [bw.value for bw in bws]
        lats_vals = [lat.value for lat in lats]
        cmap = get_cmap(color, read_ratio, read_ratios)
        ax.plot(bws_vals[:-1], lats_vals[:-1], color=cmap, linewidth=1)

    #ax.set_title(f'Bandwidth-Latency curves for {mem_type}-{mem_freq} on {machine} ({cpu})')
    return ax


def add_bws_lats(
    ax: matplotlib.axes.Axes,
    bws: list[Bandwidth],
    lats: list[Latency],
    color: str = 'black'
) -> None:
    """
    Add bandwidths and latencies to the plot.

    Args:
        ax (matplotlib.axes.Axes): axes of the plot.
        bws (list[float]): list of bandwidths to plot.
        lats (list[float]): list of latencies to plot.
        color (str): color of the points.

    Returns:
        None.
    """
    if len(bws) > 0 and len(bws) != len(lats):
        raise ValueError('The number of bandwidths and latencies must be the same.')

    if len(bws) > 0:
        bws_vals = [bw.value for bw in bws]
        lats_vals = [lat.value for lat in lats]
        ax.plot(bws_vals, lats_vals, color=color, linewidth=0, marker='o', alpha=0.4)


def save_pdf_figure(
    fig: Figure,
    filepath: str,
    default_name: str,
    verbose: bool = True
) -> None:
    """
    Save the figure in the given filepath.

    Args:
        fig (matplotlib.figure.Figure): figure to save.
        filepath (str): path to the file where the plot will be saved.
    
    Returns:
        None.
    """
    non_pdf_err_fn = lambda file_ext: (f'File extension {file_ext} for '
                                       'plotting is not supported. '
                                       'Use .pdf instead.')

    # Add .pdf extension if not present
    _, file_extension = os.path.splitext(default_name)
    if not file_extension:
        default_name += '.pdf'
    elif file_extension != '.pdf':
        raise ValueError(non_pdf_err_fn(file_extension))
    
    if not filepath:
        filepath = default_name
    else:
        if os.path.isdir(filepath):
            filepath = os.path.join(filepath, default_name)
        else:
            _, filepath_extension = os.path.splitext(filepath)
            if not filepath_extension:
                filepath += f'_{default_name}'
            elif filepath_extension == '.pdf':
                filepath = filepath.replace('.pdf', f'_{default_name}')
            else:
                raise ValueError(non_pdf_err_fn(filepath_extension))
            
    if verbose:
        print(f'Saving pdf plot in {filepath}')

    fig.savefig(filepath)


def plot_curves(
    cvs: Curves,
    bw_unit: str,
    lat_unit: str,
    bws: list[Bandwidth] = [],
    lats: list[Latency] = [],
    freq: Frequency = None,
    color: str = 'Reds',
    gradient: bool = True,
    legend_title = '',
    filepath: str = ''
) -> Figure:
    """
    Plot the curves and saves the plot in a file with the provided name.

    Args:
        cvs (Curves): Curves object to plot.
        bw_unit (str): units of bandwidth to plot.
        lat_unit (str): units of latency to plot.
        bws (list[float], optional): list of bandwidths to plot.
            Defaults to [].
        lats (list[float], optional): list of latencies to plot.
            Defaults to [].
        color (str, optional): color palette to use (e.g. Reds, Blues,
            Greens, etc.).
            You can find them here:
            https://matplotlib.org/stable/tutorials/colors/colormaps.html
        gradient (bool, optional): if True, the color of the curves will change
            depending on the read ratio.
        legend_title (str, optional): title of the legend.
        filepath (str, optional): path to the file where the plot will be saved.

    Returns:
        Matplotlib figure.
    """
    # Assume all the values in BW and Lat lists have the same units
    if bws[0].unit != bw_unit:
        bws = [bw.as_unit(bw_unit) for bw in bws]
    if lats[0].unit != lat_unit:
        lats = [lat.as_unit(lat_unit, freq) for lat in lats]

    fig, ax = plt.subplots()
    set_curves_figure(ax, cvs, bw_unit, lat_unit,
                      freq, color, gradient, legend_title)
    if len(bws) + len(lats) > 0:
        add_bws_lats(ax, bws, lats, color='black')
    fig.set_size_inches([16, 9])
    fig.tight_layout()

    if filepath:
        filename = 'curves.pdf'
        print('Saved plot:', os.path.join(filepath, filename))
        save_pdf_figure(fig, filepath, default_name=filename, verbose=False)
    
    return fig


def plot_baseline_and_target_curves(
    baseline_cvs: Curves,
    target_cvs: Curves,
    bw_unit: str,
    lat_unit: str,
    freq: Frequency = None,
    baseline_bws: list[Bandwidth] = [],
    baseline_lats: list[Latency] = [],
    target_bws: list[Bandwidth] = [],
    target_lats: list[Latency] = [],
    baseline_name: str = 'Baseline',
    target_name: str = 'Target',
    gradient: bool = True,
    filepath: str = ''
)-> Figure:
    """
    Plot the curves of the baseline and target systems and saves the
    plot in a file with the provided name.

    Args:
        baseline_cvs (Curves): Curves object of the baseline system.
        target_cvs (Curves): Curves object of the target system.
        bw_unit (str): units of bandwidth to plot.
        lat_unit (str): units of latency to plot.
        baseline_name (str): name of the baseline system.
        target_name (str): name of the target system.
        gradient (bool): if True, the color of the curves will change
            depending on the read ratio.
        filepath (str): path to the file where the plot will be saved.

    Returns:
        Matplotlib figure.
    """
    fig, ax = plt.subplots()
    baseline_color = 'Blues'
    target_color = 'Greens'

    # Assume all the values in BW and Lat lists have the same units
    if baseline_bws[0].unit != bw_unit:
        baseline_bws = [bw.as_unit(bw_unit) for bw in baseline_bws]
    if baseline_lats[0].unit != lat_unit:
        baseline_lats = [lat.as_unit(lat_unit, freq) for lat in baseline_lats]
    if len(target_bws) and target_bws[0].unit != bw_unit:
        target_bws = [bw.as_unit(bw_unit) for bw in target_bws]
    if len(target_lats) and target_lats[0].unit != lat_unit:
        target_lats = [lat.as_unit(lat_unit, freq) for lat in target_lats]

    # Baseline memory curves
    set_curves_figure(ax, baseline_cvs, bw_unit, lat_unit,
                      freq, baseline_color, gradient)
    if len(baseline_bws) + len(baseline_lats) > 0:
        add_bws_lats(ax, baseline_bws, baseline_lats, color='blue')
    
    # Target memory curves
    set_curves_figure(ax, target_cvs, bw_unit, lat_unit,
                      freq, target_color, gradient)
    if len(target_bws) + len(target_lats) > 0:
        add_bws_lats(ax, target_bws, target_lats, color='#246924')
    
    # Set legend
    set_legend_baseline_and_target_curves(ax, list(baseline_cvs.curves.keys()),
                                          baseline_color, baseline_name,
                                          list(target_cvs.curves.keys()),
                                          target_color, target_name)

    #ax.set_title(f'Bandwidth-Latency curves for {mem_type}-{mem_freq} on {machine} ({cpu})')
    fig.set_size_inches([16, 9])
    fig.tight_layout()
    
    if filepath:
        filename = 'baseline_and_target_curves.pdf'
        print('Saved plot:', os.path.join(filepath, filename))
        save_pdf_figure(fig,
                        filepath,
                        default_name=filename,
                        verbose=False)

    return fig


def plot_benchmark_results(
    results_df: pd.DataFrame,
    metric: str,
    filepath: str = ''
) -> Figure:
        """
        Plot the results of the benchmarking for the given metric and
        saves the plot in a file with the provided name.

        Args:
            results_df (pd.DataFrame): dataframe with the results of
                the benchmarking.
            metric (str): metric to plot.
            filepath (str, optional): path to the directory where the
                plot will be saved.

        Returns:
            Matplotlib figure.
        """
        filename = 'results_' + metric + '.pdf'
        fig, ax = plt.subplots(1,1)

        # Due to Python's floating problems, some values are -0 (negative zero)
        # Set values lower than epsilon to 0
        epsilon = 1e-10
        eps_filt = results_df[f'{metric}.change.min'].abs() < epsilon
        results_df.loc[eps_filt, f'{metric}.change.min'] = 0
        eps_filt = results_df[f'{metric}.change.max'].abs() < epsilon
        results_df.loc[eps_filt, f'{metric}.change.max'] = 0
        
        yerr = [results_df[f'{metric}.change.min'].tolist()] +\
               [results_df[f'{metric}.change.max'].tolist()]
        ax.bar(x=results_df['benchmark'],
               height=results_df[f'{metric}.change.avg'],
               yerr=yerr,
               capsize=3,
               width=0.5,
               color='#cccccc',
               label=f'{metric} change estimated')

        if (results_df[f'{metric}.change.avg'].mean() > 0):
            bench_label_pos_args = {'top': False,
                                    'labeltop': False,
                                    'bottom': True,
                                    'labelbottom': True}
        else:
            bench_label_pos_args = {'top': True,
                                    'labeltop': True,
                                    'bottom': False,
                                    'labelbottom': False}

        plt.rcParams['font.size'] = 13
        plt.xticks(fontsize=13)
        plt.yticks(fontsize=13)

        ax.tick_params(axis='x', rotation=90, **bench_label_pos_args)
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.set_ylabel(f'{metric} difference vs. the baseline [%]', fontsize=13)
        ax.legend()

        fig.set_size_inches([12.2,6.86])
        fig.tight_layout()

        if filepath:
            print('Saved plot:', os.path.join(filepath, filename))
            save_pdf_figure(fig, filepath, default_name=filename, verbose=False)

        return fig