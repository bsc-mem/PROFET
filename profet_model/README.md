## PROFET model code

There are four python files:

 - **main\_script**: containing the main code.
 - **model**: actual functions that implement equations from the paper, for the performance and power prediction.
 - **utilities**: containing functions for loading bandwidth-latency dependency curves, loading traces etc.
 - **measured\_results**: containing measured CPI (cycles-per-instruction) and power consumption, so the estimation error can be calculated.

Jump to a specific section:
 - [Execution instructions][]
 - [Trace files format][]
 - [Bandwidth-latency files format][]

[Execution instructions]: https://github.com/bsc-mem/PROFET/tree/master/profet_model#execution-instructions "Jump to Execution instructions section"
[Trace files format]:  https://github.com/bsc-mem/PROFET/tree/master/profet_model#trace-files-format "Jump to Trace files format section"
[Bandwidth-latency files format]: https://github.com/bsc-mem/PROFET/tree/master/profet_model#bandwidth-latency-files-format "Jump to Bandwidth-latency files format section"

### Execution instructions

The code is executed calling the main script. It has 3 parameters:

 - traces\_dir: this is the directory where the traces are located for all the benchmarks, measured on the base memory configuration.
 - mem\_confs: these are directories with bandwidth-latency dependencies of the two memory configurations (base one and the target one).
 - platform: this is the platform on which we are executing our benchmarks: snb (for Sandy Bridge) and knl (for Knights Landing).

#### Examples and expected outputs

This is the example of executing the main script for estimating performance from baseline DDR4-2400 memory system, to the target MCDRAM memory system, on a Knights Landing platform:
```
./main_script.py -traces_dir estimation_traces/DDR4-2400_trace -mem_confs bwlats/ddr4 bwlats/mcdram -platform knl
```

The program prints the estimation average, together with minimum, maximum and estimation error.
The example above prints the following output:

```
-Estimation results:
           |            Performance estimation
 benchmark |    avg   |   min  |   max  | measured |  error
............................................................
sphinx3    |  54.791% |  2.576 |  2.734 |  47.095% |  5.23%
leslie3d   | 211.755% | 11.548 | 12.072 | 211.599% |  0.05%
libquantum |  81.044% |  3.125 |  1.592 | 117.789% | 16.87%
lbm        |  69.134% |  7.964 |  9.184 | 106.786% | 18.21%
omnetpp    |  21.498% |  4.999 |  2.552 |  11.398% |  9.07%
soplex     |  27.168% |  1.705 |  1.364 |  15.610% | 10.00%
GemsFDTD   |  15.410% |  1.173 |  1.290 |  16.365% |  0.82%
milc       |   2.666% |  0.205 |  0.227 |  18.465% | 13.34%
cactusADM  |  -0.969% |  0.090 |  0.081 |   2.265% |  3.16%
gcc        |   8.846% |  1.183 |  0.552 |  16.186% |  6.32%
astar      |   3.408% |  0.932 |  0.386 |   3.965% |  0.54%
hmmer      |  -0.134% |  0.000 |  0.000 |   0.130% |  0.26%
zeusmp     |  -3.374% |  0.124 |  0.187 |   0.853% |  4.19%
xalancbmk  |  -2.463% |  0.559 |  0.385 |  -0.059% |  2.41%
bwaves     |  -1.187% |  0.058 |  0.055 |   0.655% |  1.83%
wrf        |  -2.790% |  0.185 |  0.182 |   0.266% |  3.05%
dealII     |   0.558% |  0.122 |  0.134 |   2.128% |  1.54%
h264ref    |  -1.714% |  0.039 |  0.038 |  -0.357% |  1.36%
bzip2      |  -5.968% |  0.192 |  0.281 |  -3.206% |  2.85%
mcf        | -11.086% |  0.987 |  2.272 |  -8.637% |  2.68%
gobmk      |  -1.332% |  0.032 |  0.031 |  -0.245% |  1.09%
gromacs    |  -1.038% |  0.016 |  0.016 |  -0.253% |  0.79%
sjeng      |  -1.868% |  0.045 |  0.043 |  -0.713% |  1.16%
perlbench  |  -2.887% |  0.097 |  0.091 |  -1.107% |  1.80%
tonto      |   0.747% |  0.012 |  0.008 |   1.334% |  0.58%
namd       |  -0.202% |  0.000 |  0.000 |  -0.053% |  0.15%
calculix   |  -0.906% |  0.011 |  0.011 |   0.176% |  1.08%
gamess     |  -0.074% |  0.000 |  0.000 |  -0.095% |  0.02%
povray     |  -0.050% |  0.000 |  0.000 |   0.003% |  0.05%

-Performance estimation error:
  High-bw benchmarks:      6.99%
  Low-bw benchmarks:       1.57%
```

The example for estimating performance, power and energy consumption on Sandy Bridge platform, from baseline DDR3-800 to the target DDR3-1600 memory is the following:

```
./main_script.py -traces_dir estimation_traces/DDR3-800_trace -mem_confs bwlats/ddr3-800 bwlats/ddr3-1600 -platform snb
```

And it prints the following output:

```
-Estimation results:
           |            Performance estimation              ||               Power estimation                ||               Energy estimation
 benchmark |    avg   |   min  |   max  | measured |  error ||   avg   |   min  |   max  | measured |  error ||    avg   |   min  |   max  | measured |  error
................................................................................................................................................................
libquantum |  69.909% |  2.679 |  1.279 |  80.140% |  5.68% ||  2.398% |  0.105 |  0.059 |  6.780%  |  4.10% || -39.731% |  0.419 |  0.900 | -40.724% |  1.68%
bwaves     |  53.874% |  6.790 |  7.133 |  60.602% |  4.19% ||  2.720% |  0.364 |  0.385 |  5.981%  |  3.08% || -33.192% |  2.770 |  2.783 | -34.010% |  1.24%
lbm        |  42.882% | 11.263 | 14.578 |  66.827% | 14.35% ||  2.082% |  0.571 |  0.739 |  6.147%  |  3.83% || -28.340% |  6.361 |  5.464 | -36.373% | 12.63%
milc       |  51.185% | 10.636 |  4.138 |  64.545% |  8.12% ||  2.130% |  0.466 |  0.189 |  6.297%  |  3.92% || -32.380% |  1.745 |  4.713 | -35.399% |  4.67%
soplex     |  55.876% | 10.606 |  4.391 |  57.117% |  0.79% ||  2.541% |  0.562 |  0.252 |  4.869%  |  2.22% || -34.146% |  1.716 |  4.347 | -33.254% |  1.34%
GemsFDTD   |  47.887% |  6.359 |  3.039 |  48.053% |  0.11% ||  3.328% |  0.427 |  0.220 |  4.185%  |  0.82% || -30.106% |  1.286 |  2.813 | -29.630% |  0.68%
leslie3d   |  36.691% |  2.408 |  2.604 |  29.254% |  5.75% ||  1.827% |  0.125 |  0.135 |  1.321%  |  0.50% || -25.496% |  1.305 |  1.234 | -21.611% |  4.96%
mcf        |  40.733% |  9.505 |  3.406 |  48.520% |  5.24% ||  1.948% |  0.410 |  0.149 |  3.616%  |  1.61% || -27.488% |  1.680 |  4.863 | -30.234% |  3.94%
sphinx3    |  40.422% |  2.203 |  1.629 |  29.530% |  8.41% ||  2.446% |  0.144 |  0.108 |  1.091%  |  1.34% || -27.039% |  0.766 |  1.054 | -21.956% |  6.51%
wrf        |  15.888% |  0.856 |  0.915 |  16.195% |  0.26% ||  0.778% |  0.036 |  0.038 |  0.965%  |  0.19% || -13.037% |  0.650 |  0.614 | -13.107% |  0.08%
omnetpp    |  31.587% |  8.878 |  4.944 |  27.841% |  2.93% ||  1.858% |  0.420 |  0.241 |  1.283%  |  0.57% || -22.487% |  2.733 |  5.152 | -20.775% |  2.16%
zeusmp     |  19.271% |  3.031 |  3.261 |  17.103% |  1.85% ||  1.203% |  0.110 |  0.111 |  1.206%  |  0.00% || -15.124% |  2.192 |  2.094 | -13.575% |  1.79%
cactusADM  |  17.432% |  3.472 |  4.540 |  14.018% |  2.99% ||  1.117% |  0.094 |  0.123 |  1.052%  |  0.06% || -13.855% |  3.142 |  2.503 | -11.373% |  2.80%
astar      |  17.490% |  2.997 |  0.874 |  14.397% |  2.70% ||  1.281% |  0.100 |  0.030 |  1.192%  |  0.09% || -13.786% |  0.626 |  2.159 | -11.543% |  2.54%
gcc        |  20.562% |  4.233 |  3.930 |  17.828% |  2.32% ||  2.263% |  0.787 |  0.978 | -0.286%  |  2.56% || -15.146% |  1.924 |  2.378 | -15.373% |  0.27%
dealII     |   6.790% |  0.299 |  0.227 |   2.644% |  4.04% ||  1.897% |  0.083 |  0.069 |  1.241%  |  0.65% ||  -4.581% |  0.138 |  0.189 |  -1.366% |  3.26%
bzip2      |   7.520% |  0.738 |  0.619 |   6.808% |  0.67% ||  1.137% |  0.020 |  0.015 |  0.454%  |  0.68% ||  -5.935% |  0.526 |  0.630 |  -5.949% |  0.01%
gobmk      |   2.698% |  0.108 |  0.116 |   1.899% |  0.78% ||  1.071% |  0.001 |  0.001 |  2.003%  |  0.91% ||  -1.585% |  0.110 |  0.103 |   0.102% |  1.68%
xalancbmk  |  21.594% |  3.804 |  3.687 |  18.013% |  3.03% ||  2.500% |  3.285 |  3.270 |  0.268%  |  2.23% || -15.705% |  0.086 |  0.343 | -15.036% |  0.79%
sjeng      |   3.450% |  0.131 |  0.138 |   2.205% |  1.22% ||  1.115% |  0.004 |  0.004 |  0.749%  |  0.36% ||  -2.257% |  0.134 |  0.127 |  -1.424% |  0.85%
hmmer      |   0.144% |  0.000 |  0.000 |   0.051% |  0.09% ||  1.074% |  0.001 |  0.001 |  0.239%  |  0.83% ||   0.928% |  0.002 |  0.002 |   0.188% |  0.74%
tonto      |   2.674% |  0.174 |  0.190 |   3.157% |  0.47% ||  2.600% |  0.103 |  0.112 |  0.717%  |  1.87% ||  -0.072% |  0.075 |  0.069 |  -2.365% |  2.35%
gromacs    |   0.830% |  0.008 |  0.008 |   0.914% |  0.08% ||  1.200% |  0.001 |  0.001 |  0.583%  |  0.61% ||   0.367% |  0.009 |  0.009 |  -0.328% |  0.70%
h264ref    |   0.850% |  0.009 |  0.009 |   0.264% |  0.58% ||  1.135% |  0.000 |  0.000 |  0.795%  |  0.34% ||   0.283% |  0.009 |  0.009 |   0.530% |  0.25%
calculix   |   0.700% |  0.005 |  0.005 |  -0.002% |  0.70% ||  1.219% |  0.000 |  0.000 |  3.536%  |  2.24% ||   0.515% |  0.006 |  0.006 |   3.538% |  2.92%
namd       |   0.178% |  0.000 |  0.000 |  -0.564% |  0.75% ||  1.197% |  0.000 |  0.000 |  0.252%  |  0.94% ||   1.017% |  0.000 |  0.000 |   0.821% |  0.19%
perlbench  |   4.645% |  0.219 |  0.234 |   1.227% |  3.38% ||  0.518% |  0.086 |  0.079 |  0.496%  |  0.02% ||  -3.943% |  0.297 |  0.277 |  -0.722% |  3.24%
gamess     |   0.003% |  0.000 |  0.000 |  -0.365% |  0.37% ||  1.149% |  0.001 |  0.001 |  1.521%  |  0.37% ||   1.146% |  0.001 |  0.001 |   1.893% |  0.73%
povray     |   0.002% |  0.000 |  0.000 |  -0.687% |  0.69% ||  1.145% |  0.000 |  0.000 | -0.500%  |  1.65% ||   1.144% |  0.000 |  0.000 |   0.189% |  0.95%
QE         |  40.021% |  9.054 |  5.751 |  37.269% |  2.01% ||  1.915% |  0.456 |  0.286 |  3.656%  |  1.68% || -27.113% |  2.777 |  4.582 | -24.487% |  3.48%
ALYA       |  28.541% |  4.209 |  3.641 |  35.500% |  5.14% ||  1.251% |  0.154 |  0.140 |  3.242%  |  1.93% || -21.201% |  2.093 |  2.514 | -23.807% |  3.42%
GROMACS    |   3.674% |  0.111 |  0.115 |   3.863% |  0.18% ||  0.867% |  0.001 |  0.001 |  1.126%  |  0.26% ||  -2.707% |  0.107 |  0.103 |  -2.635% |  0.07%
NAMD       |   2.738% |  0.095 |  0.092 |   1.305% |  1.41% ||  1.028% |  0.001 |  0.001 |  0.615%  |  0.41% ||  -1.665% |  0.087 |  0.090 |  -0.682% |  0.99%

-Performance estimation error:
  High-bw benchmarks:      5.00%
  Low-bw benchmarks:       1.49%

-Power estimation error:
  High-bw benchmarks:      2.10%
  Low-bw benchmarks:       0.84%

-Energy estimation error:
  High-bw benchmarks:      3.72%
  Low-bw benchmarks:       1.39%
```

Note that the estimations can be done in reverse as well, e.g. from MCDRAM to DDR4 memory, or from any higher-frequency DDR3 memory configuration to lower-frequency DDR3 memory configuration, e.g. DDR3-1600 to DDR3-800.

### Trace files format

Example trace files of benchmarks and applications are given in the **\*.csv** file format, in the [estimation\_traces](estimation\_traces/) directory. Traces for Sandy Bridge architecture have all the trace files: cycles, instructions, llc_misses, bw (measured memory bandwidth), page_stats (row-buffer access statistics), pwr_stats (statistics on power-down states) pwrs (measured power consumption) and timings (displaying duration of the benchmark execution in seconds), for each of the applications. Traces for Knights Landing comprise cycles, instructions, llc_misses, bw and timings. All types of the trace files are in separate csv files.

When executing SPEC CPU2006 benchmarks, we executed 16 copies of each benchmark on Sandy Bridge platform, and as many copies as we can on Knights Landing platform, to fit MCDRAM memory capacity.

Here are the formats of the traces:
 - **cycles**, **instructions** and **llc_misses** contain values for each CPU core, following by the sampling time at the end:

 \<CPU 0 value\>,\<CPU 1 value\>,\<CPU 2 value\>,...,\<CPU *N* value\>,\<time\>
 - **bw** trace contains values of read and write memory bandwidth (in MB/s) for each memory channel, following by the sampling time at the end:

 \<Ch0 RD value\>,\<Ch1 RD value\>,...,\<Ch*N* RD value\>,\<Ch0 WR value\>,\<Ch1 WR value\>,...,\<Ch*N* WR value\>,\<time\>
 - **page_stats** trace shows percentages of row-buffer empty, row-buffer miss and row-buffer hit accesses (of total number of accesses), per memory channel, following by a sampling time:

 \<Ch0 page empty \%\>,...,\<Ch*N* page empty \%\>,\<Ch0 page miss \%\>,...,\<Ch*N* page miss \%\>,\<Ch0 page hit \%\>,...,\<Ch*N* page hit \%\>,\<time\>
 - **pwr_stats** trace holds percentages of power-down and self-refresh DRAM cycles (of total number of DRAM cycles), per memory channel, following by a sampling time:

 \<Ch0 power-down \%\>,...,\<Ch*N* power-down \%\>,\<Ch0 self-refresh \%\>,...,\<Ch*N* self-refresh \%\>,\<time\>
 - **pwrs** trace contains power consumption value (in Watts), sampled on the same sampling period as other traces.
 - **timings** trace file shows the benchmark execution time in seconds. For SPEC CPU2006 benchmarks a single number is given, while for the UEABS HPC applications there are two numbers, marking the beginning and the end of the period of interest.

### Bandwidth-latency files format

Measured bandwidth and latency dependency for various memory configurations are located in the [bwlats](bwlats/) directory.
These dependencies were measured using [mem\_bw\_load](/mem\_bw\_load/) benchmark to generate bandwidth load, while measuring memory access latency using [mem\_acc\_lat](/mem\_acc\_lat/) benchmark. We measured total execution CPU cycles, together with page walks and secondary dtlb penalties, using **perf** tool. At the end we subtracted page walks and secondary dtlb penalties from the total number of cycles and divided the result by the number of instructions to get the final per-load memory access latency.

Each memory configuration has measured dependency for separate RD ratio from 50\% to 100\% of reads in the total traffic. All the files contain measured bandwidth (in MB/s) and latency (in CPU cycles) in the following format:

\<total bandwidth (RD+WR)\> \<latency\> &nbsp; # rd: \<measured RD bandwidth\>, wr: \<measured WR bandwidth\>
