## Memory access latency benchmark

The benchmark measures access latency of different levels of memory hierarchy, for a randomized memory access pattern (so the effect of the prefetcher is negligible).
The load file size determines in which level of memory hierarchy the load file resides and which memory hierarchy level is tested.

The benchmark is implemented as a pointer-chasing code with load instructions in x86 assembly.
Execution time or number of CPU cycles of the benchmark execution can be measured using tools such as **perf**, **LIKWID**, etc. In our experiments, we also measured page walks and secondary dtlb penalties, so we can subtract them from the total CPU cycles count and get more precise results. Afterwards, dividing this result with the number of load instructions, we can calculate per-load access latency of a certain memory hierarchy level.

#### Installing the benchmark

Installation requires **python** and a **C** compiler. We tested the code with **gcc** (higher than 4.9.1) and **Intel** compiler.

Before installing the benchmark the compiler and compiler flags can be set in **generate.py** file as `CC` and `CFLAGS` variables.
Also, the size(s) of load file(s) can be set in the `sizes` list (in kB). It can be a single size, or several sizes. For example, to set the load file size of 512MB, define the variable as `sizes = [524288]`.
Finally, number of load instructions is defined in with `ins` variable.

First, execute the **generate.py** file to generate the binary which creates the load file, and the benchmark binary which walks the random walk file.
Put the templates of the generator and benchmark files as arguments.
```
python generate.py generator.c lat_bm.c
```
The following output should be displayed for the 512MB load file:
```
Generating benchmarks for sizes: 524288kB
Done generating benchmarks.
Compiling generator files...
  gcc -O0 gen/src/00524288-gen.c -o gen/bin/00524288-gen
Done compiling.
Compiling benchmark files...
  gcc -O0 lat_bm/src/00524288.c -o lat_bm/bin/00524288
Done compiling.
```
Then, execute the created binary `gen/bin/00524288-gen`.
It creates the load file `gen/data/8388608.dat` with size of 512MB. It contains randomized access pattern used later by the pointer-chasing code.

Finally, execute the benchmark binary `lat_bm/bin/00524288`, which loads the access pattern from `gen/data/8388608.dat` and executes the pointer-chasing code.

#### Example of the benchmark execution and measurement with perf

For example, on Sandy Bridge E5-2670 platform, we used the benchmark as follows:
```
numactl -C 0 -m 0 perf stat -e cycles:u,instructions:u,r1008:u,r0408:u ./lat_bm/run/00524288
```
This way, we execute the benchmark on CPU core0 and measure cycles, instructions, hits in the secondary dtlb and page walks.
From the total number of cycles we subtract page walks and secondary dtlb penalties (7 cycles on our platform), divide this result with number of instructions (5M),
and this way we get only the latency of the random memory read access, without the cycles needed for address translation.
