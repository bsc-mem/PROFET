## Memory access latency benchmark

The benchmark measures access latency of different levels of memory hierarchy, for a randomized memory access pattern (so the effect of the prefetcher is negligible).
The load file size determines in which level of memory hierarchy the load file resides and which memory hierarchy level is tested.

The benchmark is implemented as a pointer-chasing code with load instructions in x86 assembly.
Execution time or number of CPU cycles of the benchmark execution can be measured using tools such as **perf**, **LIKWID**, etc. In our experiments, we also measured page walks and secondary dtlb penalties, so we can subtract them from the total CPU cycles count and get more precise results. Afterwards, dividing this result with the number of load instructions, we can calculate per-load access latency of a certain memory hierarchy level.

#### Installing the benchmark

Installation requires **python3** and C compiler. We tested the code with **gcc** (higher than 4.9.1) and Intel compiler.

Before installing the benchmark the compiler and compiler flags can be set in **generator.py** and **latencyasm.py** files.
Also, the size(s) of load file(s) can be set in both files, in the `sizes` list (in kB). It can be a single size, or several sizes. For example, to set the load file size of 512MB, define the variable as `sizes = [524288]`.

Finally, number of load instructions is defined in **latencyasm.py** file, with  `ins` variable.
It is defined in thousands. Therefore, to define 5M instructions, set it to 5000 `ins = 5000`.

First, execute the **generator.py** file to generate the binary which creates the load file.
```
python3 generator.py
```
The following output should be displayed for the 512MB load file:
```
Generating file for size: 524288kB
gcc -mcmodel=large gen/src/00524288-gen.c -o gen/bin/00524288-gen
Random walk file gen/bin/00524288-gen generated.
```
Then, execute the created binary `gen/bin/00524288-gen`.

It creates the load file `gen/data/8388608.dat` with size of 512MB. It contains randomized access pattern used later by the pointer-chasing code.

Now lets create our benchmark. Run the **latencyasm.py** with input template argument **lat_bm.c**:
```
python3 latencyasm.py lat_bm.c
```
It should display:
```
Generating benchmark for size: 524288kB
gcc -mcmodel=large lat_bm/src/00524288.c -o lat_bm/bin/00524288
Benchmark lat_bm/bin/00524288 generated.
```
The final benchmark `lat_bm/bin/00524288` is created.

#### Example of the benchmark execution and measurement with perf

For example, on Sandy Bridge E5-2670 platform, we used the benchmark as follows:
```
numactl -C 0 -m 0 perf stat -e cycles:u,instructions:u,r1008:u,r0408:u ./lat_bm/run/00524288
```
This way, we execute the benchmark on CPU core0 and measure cycles, instructions, hits in the secondary dtlb and page walks.
From the total number of cycles we subtract page walks and secondary dtlb penalties (7 cycles on our platform), divide this result with measured number of instructions (~5M),
and this way we get only the latency of the random memory read access, without the cycles needed for address translation.
