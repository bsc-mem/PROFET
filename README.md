# PROFET
Analytical model that quantifies the impact of the main memory on application performance.

Supplemental code for the SIGMETRICS 2019 paper ["PROFET: Modeling System Performance and Energy Without Simulating the CPU"](https://dl.acm.org/citation.cfm?id=3326149).

The [`src/profet/`](src/profet/) code contains the PROFET model. The bandwdith-latency curves must be precomputed.



## Installation

From the project's root folder, install PROFET with `pip`:
   ```
   pip install .
   ```

It automatically installs any requirements listed in [`requirements.txt`](requirements.txt).
   
After installation, it provides a CLI tool named `profet`. Additionally, it automatically creates a `profet` python package that you can use in any of your Python programs.



## CLI Tool Usage

**Description**: The CLI tool is designed to estimate system performance using two memory configurations.

**Usage**:

```
profet -a app_profiling_dir -c config_file.json --mem_base bw_lat_curves_dir [OPTIONS] [mem_target]
```

**Arguments**:
- `-a, --app_profiling`: Directory containing application profiling files.
- `-c, --config`: Configuration file (JSON) path.
- `--mem_base`: Directory containing bandwidth-latency curves for the baseline system.

**Options**:
- `--mem-target`: Directory containing bandwidth-latency dependencies for the target system.
- `-b, --benchmarking`: Application profiling directory expected to contain subdirectories with the benchmarking app profilings.
- `-p, --plot-to-pdf FILE`: Specify the location for storing the PDF plot.
- `-w, --ignore-warnings`: Ignore warning messages.


### Arguments Description

- **App Profiling**: Conducted on the baseline memory system, it involves running the application and profiling with hardware performance counters. This captures data such as CPU cycles, instruction count, last-level cache (LLC) misses, and memory read/write bandwidths. Profiling is sampled over regular intervals, called segments. Refer to Section 4.1 of of the PROFET paper.

- **Config**: This file contains CPU and DRAM parameters required for PROFET. Configuration JSON examples are available in the [`configs/`](configs/) directory.

- **Memory Base & Target**: Acquired using bandwidth-latency curves for both the baseline and target memory systems. The methodology is detailed in Section 3 of the PROFET paper, which explains the memory profiling microbenchmarks and their results.


### Execution Examples

Assuming `$PROFETPATH` contains the path to this PROFET package.


#### Baseline Plot

Generate a plot in the current directory (specified by `-p .`) that provides a summary of the bandwidth-latency for baseline profiling. It uses:
- Profiling data for the HPCG application, located at `$PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/HPCG`.
- The configuration for the system, located at `$PROFETPATH/configs/sample.json`.
- Baseline precomputed memory bandwidth-latency curves, located at `$PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/`.

```
profet -w \
-p . \
-a $PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/HPCG \
-c $PROFETPATH/configs/sample.json \
--mem-base $PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/
```



#### Baseline and Target Prediction Plot

Generate a plot, in your current folder, with a bandwidth-latency summary of the baseline profiling and the target system prediction.

Generate a plot in the current directory (specified by `-p .`) that provides a summary of the bandwidth-latency of the baseline profiling and the target system prediction. It uses:
- Profiling data for the HPCG application, located at `$PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/HPCG`.
- The configuration for the system, located at `$PROFETPATH/configs/sample.json`.
- Baseline precomputed memory bandwidth-latency curves, located at `$PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/`.
- Target precomputed memory bandwidth-latency curves, located at `$PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__upi_remote_socket/`.

```
profet -w \
-p . \
-a $PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/HPCG \
-c $PROFETPATH/configs/sample.json \
--mem-base $PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/ \
--mem-target $PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__upi_remote_socket/
```



#### Benchmarking

Generate two plots in the current directory (specified by `-p .`) of a benchmark (a collection of application profilings), summarizing the CPI and IPC performance of each application. It uses:
- Profiling data for all the benchmark applications, located at `$PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/`.
- The configuration for the system, located at `$PROFETPATH/configs/sample.json`.
- Baseline precomputed memory bandwidth-latency curves, located at `$PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/`.
- Target precomputed memory bandwidth-latency curves, located at `$PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__upi_remote_socket/`.

```
profet -w --benchmarking \
-p . \
-a $PROFETPATH/tests/app_profiles/cascade_lake__DDR4_2666__local_socket/ \
-c $PROFETPATH/configs/sample.json \
--mem-base $PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__local_socket/ \
--mem-target $PROFETPATH/data/bw_lat_curves/cascade_lake__DDR4_2666__upi_remote_socket/
```



## Python Package Usage

To use the `profet` package in your Python code:
```python
import profet
```

**Documentation**: You can find detailed documentation by opening <a href="docs/html/index.html" target="_blank">docs/html/index.html</a> in your web browser.



# Running Tests

To ensure the functionality and integrity of the software, it's recommended to execute the test suite from the projects root folder.

**Command**:
```
python tests/run_tests.py
```

The complete test suite should conclude in under 5 minutes. Please ensure all tests pass before proceeding with further operations or contributions.



# License

PROFET code is released under the BSD-3 [License](LICENSE).
