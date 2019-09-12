## Memory bandwidth load benchmark

The benchmark generates the traffic towards main memory, with two runtime parameters:
 - specific amount of RD requests (between 50\% and 100\% of reads in the total traffic, with a step of 2\%)
 - a pause that inject delays (by executing *nops*) between memory requests and thus lowers the generated bandwidth

The benchmark is based on the modified STREAM \[[1][]\] benchmark.
It uses MPI library and optional OpenMP directives.
Contrary to original STREAM benchmark, it contains only the Copy kernel and the specific kernel functions for different RD ratios are coded in x86 assembly, using AVX instructions and non-temporal stores (defined in **utils.c** file). Also, the content of the arrays at the end is not checked.

Apart from the runtime parameters, the main code located in the **stream_mpi.c** file contains array size parameter (default at 80,000,000) and number of times the kernel is executed (default is 10 times).
These parameters can be set in the code, or as compiler flags during the compilation.

At the end, the benchmark displays the generated memory bandwidth (in MB/s) as the average of all the executions.

\[1\] *John D. McCalpin. 1991-2007. STREAM: Sustainable Memory Bandwidth in High Performance Computers. Technical
Report. University of Virginia. http://www.cs.virginia.edu/stream/*

[1]: http://www.cs.virginia.edu/stream/ "Original STREAM benchmark developed by John D. McCalpin"

#### Compiling the code

In order to compile the code, set the desired compiler and its flags in the Makefile.
Optionally, array size and ntimes parameters can be set as compiler flags `-DSTREAM_ARRAY_SIZE=...` and `-DNTIMES=...`.

Compile the code by hitting `make`.

#### Running the benchmark

Here is the example of running the benchmark with 16 MPI processes, with 64\% of RD traffic and a pause of 1000.

```
mpirun -n 16 ./bin/stream_mpi.x -r 64 -p 1000
```
The **-r** parameter is the required RD ratio in the total traffic (from 50 to 100, with a step of 2), while the **-p** parameter is the introduced pause. For the maximum bandwidth, set this parameter to 0.

The example above displays the following output:

```
-------------------------------------------------------------
$ Memory bandwidth load kernel $
-------------------------------------------------------------
This system uses 8 bytes per array element.
-------------------------------------------------------------
Total Aggregate Array size = 80000000 (elements)
Total Aggregate Memory per array = 610.4 MiB (= 0.6 GiB).
Total Aggregate memory required = 1220.7 MiB (= 1.2 GiB).
Data is distributed across 16 MPI ranks
   Array size per MPI rank = 5000000 (elements)
   Memory per array per MPI rank = 38.1 MiB (= 0.0 GiB).
   Total memory per MPI rank = 76.3 MiB (= 0.1 GiB).
-------------------------------------------------------------
The kernel will be executed 10 times.
 The *average* time for the kernel (excluding the first iteration)
 will be used to compute the reported bandwidth.
-------------------------------------------------------------
Your timer granularity/precision appears to be 1 microseconds.
Each test below will take on the order of 15272 microseconds.
   (= 15272 timer ticks)
Increase the size of the arrays if this shows that
you are not getting at least 20 timer ticks per test.
(WARNING -- The above is only a rough guideline.
For best results, please be sure you know the
precision of your system timer.)
-------------------------------------------------------------

Measurements:
                  Percentage of RD traffic    Pause      Avg  BW      Min  BW      Max  BW
Memory BW load               64                1000       8307.5       7832.0       8385.8
```

The average generated memory bandwidth from NTIMES iterations is 8307.5 MB/s.
The highest bandwidth during NTIMES iterations was 8385.8 MB/s while the lowest was 7832.0 MB/s.
For the best precision, memory bandwidth can be measured using uncore counters (with tools such as **perf**, **LIKWID**, etc.), which we used to get bandwidth-latency dependencies in PROFET model.

The code is currently tested with Intel compiler and Intel MPI library only.
