################################################################################
# Copyright (c) 2019, Milan Radulovic
#                     Rommel Sanchez Verdejo
#                     Paul Carpenter
#                     Petar Radojkovic
#                     Bruce Jacob
#                     Eduard Ayguade
#                     Contact: milan.radulovic [at] bsc [dot] es
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#     * Neither the name of the copyright holder nor the names
#       of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
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

# Sandy Bridge parameters
Ins_ROB_snb = 168.
IPC_max_snb = 4.
Lat_LLC_snb = 45.
MSHR_snb = 10.

# Knights Landing parameters
Ins_ROB_knl = 72.
IPC_max_knl = 2.
Lat_LLC_knl = 17.
MSHR_knl = 12.

# DRAM timings
tCK =     { '800': 2.5,  '1066': 1.875,  '1333': 1.5,  '1600': 1.25  }
tRC =     { '800': 52.5, '1066': 50.625, '1333': 49.5, '1600': 48.75 }
tRC_cyc = { '800': 21.0, '1066': 27.0,   '1333': 33.0, '1600': 39.0  }
tRAS =    { '800': 37.5, '1066': 37.5,   '1333': 36.0, '1600': 35.0  }
tRRD =    { '800': 10.0, '1066': 7.5,    '1333': 6.0,  '1600': 6.0   }
tRRDsch = { '800': 10.0, '1066': 7.5,    '1333': 6.0,  '1600': 6.0   }
tRCD =    { '800': 15.0, '1066': 13.125, '1333': 13.5, '1600': 13.75 }
tCL =     { '800': 15.0, '1066': 13.125, '1333': 13.5, '1600': 13.75 }
tRP =     { '800': 15.0, '1066': 13.125, '1333': 13.5, '1600': 13.75 }
tRTP =    { '800': 10.0, '1066': 7.5,    '1333': 7.5,  '1600': 7.5   }
tRFC =    160.0
tREFI =   7.8

# DRAM powers
Idd0 =   { '800': 1296.0*1296.0/1386.0, '1066': 1296.0, '1333': 1386.0, '1600': 1476.0 }
Idd1 =   { '800': 1476.0*1476.0/1566.0, '1066': 1476.0, '1333': 1566.0, '1600': 1656.0 }
Idd2p0 = { '800': 432.0,                '1066': 432.0,  '1333': 432.0,  '1600': 432.0  }
Idd2p1 = { '800': 972.0*972.0/1152.0,   '1066': 972.0,  '1333': 1152.0, '1600': 1332.0 }
Idd3p =  { '800': 1440.0*1440.0/1620.0, '1066': 1440.0, '1333': 1620.0, '1600': 1800.0 }
Idd2n =  { '800': 1188.0*1188.0/1368.0, '1066': 1188.0, '1333': 1368.0, '1600': 1548.0 }
Idd3n =  { '800': 1620.0*1620.0/1800.0, '1066': 1620.0, '1333': 1800.0, '1600': 1980.0 }
Idd4r =  { '800': 2286.0*2286.0/2484.0, '1066': 2286.0, '1333': 2484.0, '1600': 2754.0 }
Idd4w =  { '800': 2016.0*2016.0/2286.0, '1066': 2016.0, '1333': 2286.0, '1600': 2556.0 }
Idd5b =  { '800': 3546.0*3546.0/3636.0, '1066': 3546.0, '1333': 3636.0, '1600': 3726.0 }
Idd6  =  { '800': 432.0,                '1066': 432.0,  '1333': 432.0,  '1600': 432.0  }

dram_voltage_max = 1.575
dram_voltage_normal = 1.5
dimms_no = 8.0
BL = 8.0
devices_no = 36.0 # dual-rank DIMM, 18 devices on each side
ranks_no = 2.0    # ranks per DIMM

P_term_rd = 4.7  # in mW
P_term_wr = 13.0 # in mW
DQ_rd = 90.0
DQ_wr = 90.0

# Get the latency from bandwidth, using bw-lat dependency
def get_lat_array(bw, bw_array, lat_array):
    """
    Returns the latency for measured bandwidth using bandwidth-latency dependency.
    @params:
     bw        - Required : measured bandwidth (Float)
     bw_array  - Required : array of measured bandwidths for bw-lat dependency (List of floats)
     lat_array - Required : array of measured latencies for bw-lat dependency (List of floats)

    """
    if bw > bw_array[len(bw_array)-1]:
        return lat_array[len(bw_array)-1]
    i = 0
    while bw > bw_array[i]:
        i+=1
        if i == len(bw_array):
            return 0

    if i == 0:
        return lat_array[0]
    else:
        bw_percent = ( bw - bw_array[i-1] )/( bw_array[i] - bw_array[i-1] )
        latency = lat_array[i-1] + bw_percent*(lat_array[i] - lat_array[i-1])
        return latency

# Iterate to find bandwidth on different memory configuration
def calc_perf( platform, bwlats_2_bw, bwlats_2_lat, BW_used_1, Ratio_RW_1, Cyc_tot_1, Miss_LLC, Ins_tot_1, bwlats_1_bw, bwlats_1_lat, Ins_ooo_percentage_def ):
    """
    Calculates performance on a new memory configuration.
    @params:
        platform               - Required : platform name (Str)
        bwlats_2_bw            - Required : array of measured bandwidths for bw-lat dep. for mem. conf. 2 (List of floats)
        bwlats_2_lat           - Required : array of measured latencies for bw-lat dep. for mem. conf. 2 (List of floats)
        BW_used_1              - Required : measured sample of used bandwidth on mem. conf. 1 (Float)
        Ratio_RW_1             - Required : ratio of reads in used bandwidth on mem. conf. 1 (Float)
        Cyc_tot_1              - Required : measured sample of cycles on mem. conf. 1 (Float)
        Miss_LLC               - Required : measured sample of LLC misses on mem. conf. 1 (Float)
        Ins_tot_1              - Required : measured sample of instructions on mem. conf. 1 (Float)
        bwlats_1_bw            - Required : array of measured bandwidths for bw-lat dep. for mem. conf. 1 (List of floats)
        bwlats_1_lat           - Required : array of measured latencies for bw-lat dep. for mem. conf. 1 (List of floats)
        Ins_ooo_percentage_def - Required : defined percentage of i_ooo parameter (Float)

    """

    # initialization
    bisection_error = 1.
    if platform == 'snb':
        bisection_upper_limit = 2.2*BW_used_1
    else:
        bisection_upper_limit = 7.2*BW_used_1
    bisection_lower_limit = 10.
    iter_count = 0

    # assign appropriate platform values for ROB, IPC_max, Lat_LLC and MSHR
    if platform == 'snb':
        Ins_ROB = Ins_ROB_snb
        IPC_max = IPC_max_snb
        Lat_LLC = Lat_LLC_snb
        MSHR = MSHR_snb
    else:
        Ins_ROB = Ins_ROB_knl
        IPC_max = IPC_max_knl
        Lat_LLC = Lat_LLC_knl
        MSHR = MSHR_knl

    Ratio_RW = int(round(Ratio_RW_1*100/2))*2
    if Ratio_RW < 50:
        Ratio_RW = 50

    # find Lat_mem^(1) from BW_used^(1) and Ratio_RW
    Lat_mem_1 = get_lat_array(BW_used_1, bwlats_1_bw[(Ratio_RW-50)/2], bwlats_1_lat[(Ratio_RW-50)/2])

    llc_miss_distance_ins = Ins_tot_1/Miss_LLC
    llc_miss_distance_cyc = Cyc_tot_1/Miss_LLC
    misses_per_ins = Miss_LLC/Ins_tot_1
    IPC_tot_1 = Ins_tot_1/Cyc_tot_1
    CPI_tot_1 = Cyc_tot_1/Ins_tot_1

    # Ins_ooo upper limit, equation 10
    Ins_ooo_percentage_max = ( Lat_mem_1 - Lat_LLC ) * IPC_tot_1 * 1/Ins_ROB

    if Ins_ooo_percentage_max > 1.:
        Ins_ooo_percentage_max = 1.

    # Ins_ooo parameter lower limit
    Ins_ooo_percentage_min = 0.

    # perform sensitivity analysis on Ins_ooo, using Ins_ooo_percentage_def parameter (goes from 0 to 1 in 10 steps)
    Ins_ooo_percentage = Ins_ooo_percentage_min + Ins_ooo_percentage_def * ( Ins_ooo_percentage_max - Ins_ooo_percentage_min )

    # MLP, point estimate, equation 15
    MLP_pe = 1. + Ins_ooo_percentage * Ins_ROB*misses_per_ins

    # calculate MLP_min, using sweep analysis for CPI_iter from 1/IPC_max to CPI_tot_1, in 10 steps
    CPI_iter = 1.01*1/IPC_max
    CPI_step = (CPI_tot_1 - 1/IPC_max)/10.
    MLP_min = MSHR
    while CPI_iter <= CPI_tot_1:
        if (CPI_tot_1 - CPI_iter) == 0.:
            MLP_iter = MSHR
        else:
            # calculate MLP_min, equation 14
            MLP_iter = ( Miss_LLC/Ins_tot_1 * ( Lat_mem_1 - Lat_LLC - CPI_iter * Ins_ooo_percentage*Ins_ROB ) ) / ( CPI_tot_1 - CPI_iter )
        CPI_iter += CPI_step
        if MLP_iter < MLP_min:
            MLP_min = MLP_iter

    MLP = max([MLP_pe, MLP_min])

    # calculate CPI_tot_2 on a new memory configuration, using bisection method
    while bisection_error > 0.01:
        bw_iteration = (bisection_lower_limit + bisection_upper_limit)/2.
        # get latency from bandwidth-latency dependency
        Lat_mem_2 = get_lat_array(bw_iteration, bwlats_2_bw[(Ratio_RW-50)/2], bwlats_2_lat[(Ratio_RW-50)/2])

        # calculate CPI_tot_2 and BW_used_2, equations 16 and 18
        CPI_tot_2 = CPI_tot_1 + misses_per_ins * 1.0/MLP * ( Lat_mem_2 - Lat_mem_1 )
        BW_used_2 = BW_used_1*CPI_tot_1/CPI_tot_2

        if iter_count > 1500:
            # the result is not converging: it may happen in rare cases;
            return BW_used_1, CPI_tot_1, -1
        else:
            iter_count += 1

        bisection_error = abs(bw_iteration - BW_used_2)
        if (BW_used_2 < bw_iteration and BW_used_2 > 0):
            bisection_upper_limit = bw_iteration
        else:
            bisection_lower_limit = bw_iteration

    if BW_used_2 > bwlats_2_bw[(Ratio_RW-50)/2][len(bwlats_2_bw[(Ratio_RW-50)/2])-1]:
        BW_used_2 = bwlats_2_bw[(Ratio_RW-50)/2][len(bwlats_2_bw[(Ratio_RW-50)/2])-1]

    if CPI_tot_2 < 1/IPC_max:
        CPI_tot_2 = 1/IPC_max

    return CPI_tot_2, BW_used_2, 1

# Calculate power consumption on different memory configuration
def calc_pwr( BW_used_rd_1, BW_used_wr_1, p_empty_1, p_miss_1, p_hit_1, t_ppd_1, t_sr_1, P_tot_1, mem_conf_names, BW_used_rd_2, BW_used_wr_2 ):
    """
    Calculates power on a new memory configuration.
    @params:
        BW_used_rd_1           - Required : measured sample of used read bandwidth on mem. conf. 1 (Float)
        BW_used_wr_1           - Required : measured sample of used write bandwidth on mem. conf. 1 (Float)
        p_empty_1              - Required : measured sample of a percentage of empty page accesses on mem. conf. 1 (Float)
        p_miss_1               - Required : measured sample of a percentage of page miss accesses on mem. conf. 1 (Float)
        p_hit_1                - Required : measured sample of a percentage of page hit accesses on mem. conf. 1 (Float)
        t_ppd_1                - Required : measured sample of a percentage of time spent in precharge power-down state on mem. conf. 1 (Float)
        t_sr_1                 - Required : measured sample of a percentage of time spent in self-refresh state on mem. conf. 1 (Float)
        P_tot_1                - Required : measured sample of total power consumption on mem. conf. 1 (Float)
        mem_conf_names         - Required : names of the memory configurations, e.g. '800', '1600', 'ddr4', 'mcdram' etc. (List of str)
        BW_used_rd_2           - Required : calculated used read bandwidth on mem. conf. 2 (Float)
        BW_used_wr_2           - Required : calculated used write bandwidth on mem. conf. 2 (Float)

    """

    mem_conf_lookup = {'ddr3-800'  : '800',
                       'ddr3-1066' : '1066',
                       'ddr3-1333' : '1333',
                       'ddr3-1600' : '1600'
                      }

    mem_conf_1 = mem_conf_lookup[mem_conf_names[0]]
    mem_conf_2 = mem_conf_lookup[mem_conf_names[1]]


    # calculation of different parameters from Micron's power consumption guide TN-41-01
    CASno = 1 / ( 1 - p_hit_1 )

    P_read_mem1     = ( (Idd4r[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - Idd3n[mem_conf_1]/ranks_no/1000.0 )*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_read_mem2     = ( (Idd4r[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - Idd3n[mem_conf_2]/ranks_no/1000.0 )*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_write_mem1    = ( (Idd4w[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - Idd3n[mem_conf_1]/ranks_no/1000.0 )*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_write_mem2    = ( (Idd4w[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - Idd3n[mem_conf_2]/ranks_no/1000.0 )*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_rpmiss_mem1 = ( (Idd0[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - ( Idd3n[mem_conf_1]/ranks_no/1000.0*tRAS[mem_conf_1] \
                       + Idd2n[mem_conf_1]/ranks_no/1000.0*(tRC[mem_conf_1]-tRAS[mem_conf_1])) / tRC[mem_conf_1] + ((Idd4r[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - Idd3n[mem_conf_1]/ranks_no/1000.0 )*BL/2*tCK[mem_conf_1] / tRC[mem_conf_1] ) \
                       * dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_rpmiss_mem2 = ( (Idd0[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - ( Idd3n[mem_conf_2]/ranks_no/1000.0*tRAS[mem_conf_2] \
                       + Idd2n[mem_conf_2]/ranks_no/1000.0*(tRC[mem_conf_2]-tRAS[mem_conf_2])) / tRC[mem_conf_2] + ((Idd4r[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - Idd3n[mem_conf_2]/ranks_no/1000.0 )*BL/2*tCK[mem_conf_2] / tRC[mem_conf_2] ) \
                       * dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_wpmiss_mem1 = ( (Idd0[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - ( Idd3n[mem_conf_1]/ranks_no/1000.0*tRAS[mem_conf_1] \
                       + Idd2n[mem_conf_1]/ranks_no/1000.0*(tRC[mem_conf_1]-tRAS[mem_conf_1])) / tRC[mem_conf_1] + ((Idd4w[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no)/1000.0 - Idd3n[mem_conf_1]/ranks_no/1000.0 )*BL/2*tCK[mem_conf_1] / tRC[mem_conf_1] ) \
                       * dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_wpmiss_mem2 = ( (Idd0[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - ( Idd3n[mem_conf_2]/ranks_no/1000.0*tRAS[mem_conf_2] \
                       + Idd2n[mem_conf_2]/ranks_no/1000.0*(tRC[mem_conf_2]-tRAS[mem_conf_2])) / tRC[mem_conf_2] + ((Idd4w[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no)/1000.0 - Idd3n[mem_conf_2]/ranks_no/1000.0 )*BL/2*tCK[mem_conf_2] / tRC[mem_conf_2] ) \
                       * dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    E_hit_rd_1  = P_read_mem1*BL/2*tCK[mem_conf_1]

    E_miss_rd_1 = P_rpmiss_mem1*tRC[mem_conf_1]

    E_term_rd_1 = P_term_rd*DQ_rd/1000.0*BL/2*tCK[mem_conf_1]

    E_hit_rd_2  = P_read_mem2*BL/2*tCK[mem_conf_2]

    E_miss_rd_2 = P_rpmiss_mem2*tRC[mem_conf_2]

    E_term_rd_2 = P_term_rd*DQ_rd/1000.0*BL/2*tCK[mem_conf_2]


    E_hit_wr_1  = P_read_mem1*BL/2*tCK[mem_conf_1]

    E_miss_wr_1 = P_wpmiss_mem1*tRC[mem_conf_1]

    E_term_wr_1 = P_term_wr*DQ_wr/1000.0*BL/2*tCK[mem_conf_1]

    E_hit_wr_2  = P_read_mem2*BL/2*tCK[mem_conf_2]

    E_miss_wr_2 = P_wpmiss_mem2*tRC[mem_conf_2]

    E_term_wr_2 = P_term_wr*DQ_wr/1000.0*BL/2*tCK[mem_conf_2]

    # calculate P_rd and P_wr using equations 28 -- 31
    P_rd_1 = BW_used_rd_1/1000. * ( E_miss_rd_1 * ( p_miss_1 + p_empty_1 ) + E_hit_rd_1 * ( p_hit_1 ) + E_term_rd_1 )/1000.0*16.0*1.024*1.024

    P_rd_2 = BW_used_rd_2/1000. * ( E_miss_rd_2 * ( p_miss_1 + p_empty_1 ) + E_hit_rd_2 * ( p_hit_1 ) + E_term_rd_2 )/1000.0*16.0*1.024*1.024

    P_wr_1 =  BW_used_wr_1/1000. * ( E_miss_wr_1 * ( p_miss_1 + p_empty_1 ) + E_hit_wr_1 * ( p_hit_1 ) + E_term_wr_1 )/1000.0*16.0*1.024*1.024

    P_wr_2 =  BW_used_wr_2/1000. * ( E_miss_wr_2 * ( p_miss_1 + p_empty_1 ) + E_hit_wr_2 * ( p_hit_1 ) + E_term_wr_2 )/1000.0*16.0*1.024*1.024

    # Active standby
    P_stb_1      = Idd3n[mem_conf_1]/ranks_no/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_stb_2      = Idd3n[mem_conf_2]/ranks_no/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    # PPD and SR time percentages are measured per channel, therefore both ranks
    P_ppd_1      = Idd2p1[mem_conf_1]/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_ppd_2      = Idd2p1[mem_conf_2]/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_sr_1       = Idd6[mem_conf_1]/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_sr_2       = Idd6[mem_conf_2]/1000.0*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2

    P_ref_1      = (Idd5b[mem_conf_1] - Idd2p0[mem_conf_1]/ranks_no - Idd3n[mem_conf_1]/ranks_no)/1000.0*tRFC/(tREFI*1000.0)*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2
    P_ref_2      = (Idd5b[mem_conf_2] - Idd2p0[mem_conf_2]/ranks_no - Idd3n[mem_conf_2]/ranks_no)/1000.0*tRFC/(tREFI*1000.0)*dram_voltage_max*(dram_voltage_normal/dram_voltage_max)**2


    # calculate P_tot_2
    P_tot_2 = P_tot_1 - ( P_ppd_1*(t_ppd_1 - t_sr_1) + P_sr_1*(t_sr_1) + ( 1 - t_ppd_1 )*( P_stb_1 + P_ref_1 )*ranks_no )*dimms_no \
                      + ( P_ppd_2*(t_ppd_1 - t_sr_1) + P_sr_2*(t_sr_1) + ( 1 - t_ppd_1 )*( P_stb_2 + P_ref_2 )*ranks_no )*dimms_no \
                      - P_rd_1 - P_wr_1 + P_rd_2 + P_wr_2

    return P_tot_2
