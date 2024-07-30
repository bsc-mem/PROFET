# Configuration Files for PROFET

This directory contains JSON configuration files used for setting up and running PROFET. The provided configurations specify key parameters for the CPU and DRAM.

## Sample Configuration

The [sample.json](sample.json) file includes the configuration parameters for the CPU and DRAM. Below is an explanation of these parameters:

### CPU Config

- **Description**: Describes the CPU model. Informational only, has no impact on execution.
- **Ins_ROB**: Re-order buffer (ROB) capacity.
- **IPC_max**: Maximum theoretical instructions per cycle (IPC).
- **Lat_LLC**: Last-level cache latency.
- **MSHR**: Miss status handling register capacity.


### Memory Config (optional)

- **Description**: Describes the DRAM model. Informational only, has no impact on execution.
- **Freq_MHz**: DRAM frequency in MHz.

The memory configuration specifies parameters used for plotting PROFET results. The DRAM frequency is used to calculate and display the latency in nanoseconds. If the DRAM frequency is not provided, the latency will be displayed in CPU cycles.


## Adding New Configurations

To add a new configuration, create a new JSON file following the structure of [sample.json](sample.json). Ensure that all necessary parameters are included to avoid any errors during the PROFET execution.


# References

For more information on the parameters and their impact on performance modeling, please refer to the [PROFET paper](https://dl.acm.org/citation.cfm?id=3326149), particularly Section 4.3 for CPU configurations.