# PROFET
Analytical model that quantifies the impact of the main memory on application performance and system power and energy consumption.

Supplemental code for the SIGMETRICS 2019 paper ["PROFET: Modeling System Performance and Energy Without Simulating the CPU"](https://dl.acm.org/citation.cfm?id=3326149).

The code contains the PROFET model code and the benchmarks for generating bandwdith-latency curves:

 - The directory [profet\_model](profet\_model/) contains the code for generating estimation results from the paper.
It includes bandwidth-latency curves for different memory configurations and the trace files of benchmarks used in the evaluations from the paper.
   - Note: trace files are uncompressed and consume ~380 MB.
 - In the directory [mem\_bw\_load](mem\_bw\_load/) is the code for generating memory bandwidth load, for different RD traffic ratios and bandwidth intensity.
 - The directory [mem\_acc\_lat](mem\_acc\_lat/) provides the code for measuring memory access latency, for random memory access pattern and different levels of memory hierarchy.

In each directory there are further explanations and instructions for each of the codes.

The PROFET code is released under the BSD-3 [License](LICENSE).
