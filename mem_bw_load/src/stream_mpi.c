/*------------------------------------------------------------------------------
* Copyright (c) 2019, Milan Radulovic
*                     Rommel Sanchez Verdejo
*                     Paul Carpenter
*                     Petar Radojkovic
*                     Bruce Jacob
*                     Eduard Ayguade
*                     Contact: milan.radulovic [at] bsc [dot] es
* All rights reserved.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
*     * Redistributions of source code must retain the above copyright notice,
*       this list of conditions and the following disclaimer.
*
*     * Redistributions in binary form must reproduce the above copyright
*       notice, this list of conditions and the following disclaimer in the
*       documentation and/or other materials provided with the distribution.
*
*     * Neither the name of the copyright holder nor the names
*       of its contributors may be used to endorse or promote products
*       derived from this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
------------------------------------------------------------------------------*/

# define _XOPEN_SOURCE 600

# include <stdio.h>
# include <stdlib.h>
# include <unistd.h>
# include <math.h>
# include <float.h>
# include <string.h>
# include <limits.h>
# include <sys/time.h>
# include "mpi.h"
# include "utils.h"

/*-----------------------------------------------------------------------
 * We kept most of the comments from the original STREAM code.
 *
 * INSTRUCTIONS:
 *
 *	1) Benchmark requires different amounts of memory to run on different
 *     systems, depending on both the system cache size(s) and the
 *     granularity of the system timer.
 *     You should adjust the value of 'STREAM_ARRAY_SIZE' (below)
 *     to meet *both* of the following criteria:
 *       (a) Each array must be at least 4 times the size of the
 *           available cache memory. In practice, the minimum array size
 *           is about 3.8 times the cache size.
 *           Example 1: One Xeon E3 with 8 MB L3 cache
 *               STREAM_ARRAY_SIZE should be >= 4 million, giving
 *               an array size of 30.5 MB and a total memory requirement
 *               of 91.5 MB.
 *           Example 2: Two Xeon E5's with 20 MB L3 cache each (using OpenMP)
 *               STREAM_ARRAY_SIZE should be >= 20 million, giving
 *               an array size of 153 MB and a total memory requirement
 *               of 458 MB.
 *       (b) The size should be large enough so that the 'timing calibration'
 *           output by the program is at least 20 clock-ticks.
 *           Example: most versions of Windows have a 10 millisecond timer
 *               granularity.  20 "ticks" at 10 ms/tic is 200 milliseconds.
 *               If the chip is capable of 10 GB/s, it moves 2 GB in 200 msec.
 *               This means the each array must be at least 1 GB, or 128M elements.
 *
 *      Version 5.10 increases the default array size from 2 million
 *          elements to 10 million elements in response to the increasing
 *          size of L3 caches.  The new default size is large enough for caches
 *          up to 20 MB.
 *      Version 5.10 changes the loop index variables from "register int"
 *          to "ssize_t", which allows array indices >2^32 (4 billion)
 *          on properly configured 64-bit systems.  Additional compiler options
 *          (such as "-mcmodel=medium") may be required for large memory runs.
 *
 *      Array size can be set at compile time without modifying the source
 *          code for the (many) compilers that support preprocessor definitions
 *          on the compile line.  E.g.,
 *                icc -O -DSTREAM_ARRAY_SIZE=100000000 stream_mpi.c -o stream_mpi.100M
 *          will override the default size of 80M with a new size of 100M elements
 *          per array.
 */

#ifndef STREAM_ARRAY_SIZE
#   define STREAM_ARRAY_SIZE	80000000
#endif

/*  2) Benchmark runs the kernel "NTIMES" times and reports the *avg* result
 *         for any iteration after the first, therefore the minimum value
 *         for NTIMES is 2.
 *      There are no rules on maximum allowable values for NTIMES, but
 *         values larger than the default are unlikely to noticeably
 *         increase the reported performance.
 *      NTIMES can also be set on the compile line without changing the source
 *         code using, for example, "-DNTIMES=7".
 */

#ifdef NTIMES
#if NTIMES<=1
#   define NTIMES	10
#endif
#endif
#ifndef NTIMES
#   define NTIMES	10
#endif

# define HLINE "-------------------------------------------------------------\n"

# ifndef MIN
    # define MIN(x,y) ((x)<(y)?(x):(y))
# endif
# ifndef MAX
    # define MAX(x,y) ((x)>(y)?(x):(y))
# endif

#ifndef STREAM_TYPE
    #define STREAM_TYPE double
#endif

// Some compilers require an extra keyword to recognize the "restrict" qualifier.
double * __restrict a, * __restrict b;
ssize_t array_elements, array_bytes, array_alignment;
static double	avgtime = 0, maxtime = 0, mintime = FLT_MAX;
static char	*label = "Memory BW load";

static double	bytes = 2 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
char *usage = "[-r <read_ratio>] [-p <pause>]\n";

void (*STREAM_copy_rw)(double *a_array, double *b_array,
                         ssize_t *array_size, int *pause) = NULL;

#ifdef _OPENMP
    extern int omp_get_num_threads();
#endif

int main(int argc, char *argv[])
{
    int quantum, checktick();
    int BytesPerWord, i, k, rd_ratio = 50, opt;
    ssize_t j;
    double t, times[NTIMES];
    double *TimesByRank;
    double t0,t1,tmin;
    int rc, numranks, myrank, pause = 0;

    /* --- SETUP --- call MPI_Init() before anything else! --- */
    rc = MPI_Init(NULL, NULL);
    t0 = MPI_Wtime();
    if (rc != MPI_SUCCESS)
    {
        printf("ERROR: MPI Initialization failed with return code %d\n",rc);
        exit(1);
    }

    // if either of these fail there is something really screwed up!
    MPI_Comm_size(MPI_COMM_WORLD, &numranks);
    MPI_Comm_rank(MPI_COMM_WORLD, &myrank);

    // Command line parsing
    while (( opt = getopt(argc, argv, ":r:p:")) != -1)
    {
        switch(opt)
        {
            case 'r':
                rd_ratio = atoi(optarg);
                if (rd_ratio < 50 || rd_ratio > 100 || rd_ratio % 2 == 1)
                {
                    if (myrank == 0)
                        printf("ERROR: RD ratio has to be even number between 50 and 100.\n");
                    MPI_Finalize();
                    exit(-1);
                }
                break;
            case 'p':
                pause = atoi(optarg);
                if (pause < 0)
                {
                    if (myrank == 0)
                        printf("ERROR: Pause has to be a non-negative number.\n");
                    MPI_Finalize();
                    exit(-1);
                }
                break;
            default:
                if (myrank == 0)
                    print_usage(argv, usage);
                MPI_Finalize();
                exit(-1);
        }
    }

    if (optind < argc || argc != 5)
    {
        if (myrank == 0)
            print_usage(argv, usage);
        MPI_Finalize();
        exit(-1);
    }

    // End of command line partsing

    // Assigning the right asm function based on the RD ratio
    switch(rd_ratio)
    {
        case 50:
            STREAM_copy_rw = &STREAM_copy_50;
            bytes = 2 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 52:
            STREAM_copy_rw = &STREAM_copy_52;
            bytes = 1.9230769230 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 54:
            STREAM_copy_rw = &STREAM_copy_54;
            bytes = 1.8518518510 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 56:
            STREAM_copy_rw = &STREAM_copy_56;
            bytes = 1.7857142850 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 58:
            STREAM_copy_rw = &STREAM_copy_58;
            bytes = 1.7241379310 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 60:
            STREAM_copy_rw = &STREAM_copy_60;
            bytes = 1.6666666660 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 62:
            STREAM_copy_rw = &STREAM_copy_62;
            bytes = 1.6129032250 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 64:
            STREAM_copy_rw = &STREAM_copy_64;
            bytes = 1.5625000000 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 66:
            STREAM_copy_rw = &STREAM_copy_66;
            bytes = 1.5151515150 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 68:
            STREAM_copy_rw = &STREAM_copy_68;
            bytes = 1.4705882350 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 70:
            STREAM_copy_rw = &STREAM_copy_70;
            bytes = 1.4285714280 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 72:
            STREAM_copy_rw = &STREAM_copy_72;
            bytes = 1.3888888880 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 74:
            STREAM_copy_rw = &STREAM_copy_74;
            bytes = 1.3513513510 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 76:
            STREAM_copy_rw = &STREAM_copy_76;
            bytes = 1.3157894730 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 78:
            STREAM_copy_rw = &STREAM_copy_78;
            bytes = 1.2820512820 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 80:
            STREAM_copy_rw = &STREAM_copy_80;
            bytes = 1.2500000000 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 82:
            STREAM_copy_rw = &STREAM_copy_82;
            bytes = 1.2195121950 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 84:
            STREAM_copy_rw = &STREAM_copy_84;
            bytes = 1.1904761900 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 86:
            STREAM_copy_rw = &STREAM_copy_86;
            bytes = 1.1627906970 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 88:
            STREAM_copy_rw = &STREAM_copy_88;
            bytes = 1.1363636360 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 90:
            STREAM_copy_rw = &STREAM_copy_90;
            bytes = 1.1111111110 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 92:
            STREAM_copy_rw = &STREAM_copy_92;
            bytes = 1.0869565210 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 94:
            STREAM_copy_rw = &STREAM_copy_94;
            bytes = 1.0638297870 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 96:
            STREAM_copy_rw = &STREAM_copy_96;
            bytes = 1.0416666660 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 98:
            STREAM_copy_rw = &STREAM_copy_98;
            bytes = 1.0204081630 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        case 100:
            STREAM_copy_rw = &STREAM_copy_100;
            bytes = 1 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
            break;
        default:
            STREAM_copy_rw = &STREAM_copy_50;
            bytes = 2 * sizeof(STREAM_TYPE) * STREAM_ARRAY_SIZE;
    }


    /* --- distribute requested storage across MPI ranks --- */
    array_elements = STREAM_ARRAY_SIZE / numranks;              // don't worry about rounding vs truncation
    array_alignment = 64;                                       // Can be modified -- provides partial support for adjusting relative alignment

    // Dynamically allocate the three arrays using "posix_memalign()"
    array_bytes = array_elements * sizeof(STREAM_TYPE);
    k = posix_memalign((void **)&a, array_alignment, array_bytes);
    if (k != 0)
    {
        printf("Rank %d: Allocation of array a failed, return code is %d\n",myrank,k);
        MPI_Abort(MPI_COMM_WORLD, 2);
        exit(1);
    }
    k = posix_memalign((void **)&b, array_alignment, array_bytes);
    if (k != 0)
    {
        printf("Rank %d: Allocation of array b failed, return code is %d\n",myrank,k);
        MPI_Abort(MPI_COMM_WORLD, 2);
        exit(1);
    }

    // Initial informational printouts -- rank 0 handles all the output
    if (myrank == 0)
    {
        printf(HLINE);
        printf("$ Memory bandwidth load kernel $\n");
        printf(HLINE);
        BytesPerWord = sizeof(STREAM_TYPE);
        printf("This system uses %d bytes per array element.\n",
        BytesPerWord);

        printf(HLINE);
        #ifdef N
            printf("*****  WARNING: ******\n");
            printf("      It appears that you set the preprocessor variable N when compiling this code.\n");
            printf("      This version of the code uses the preprocesor variable STREAM_ARRAY_SIZE to control the array size\n");
            printf("      Reverting to default value of STREAM_ARRAY_SIZE=%llu\n",(unsigned long long) STREAM_ARRAY_SIZE);
            printf("*****  WARNING: ******\n");
        #endif

        printf("Total Aggregate Array size = %llu (elements)\n" , (unsigned long long) STREAM_ARRAY_SIZE);
        printf("Total Aggregate Memory per array = %.1f MiB (= %.1f GiB).\n",
          BytesPerWord * ( (double) STREAM_ARRAY_SIZE / 1024.0/1024.0),
          BytesPerWord * ( (double) STREAM_ARRAY_SIZE / 1024.0/1024.0/1024.0));
        printf("Total Aggregate memory required = %.1f MiB (= %.1f GiB).\n",
          (2.0 * BytesPerWord) * ( (double) STREAM_ARRAY_SIZE / 1024.0/1024.),
          (2.0 * BytesPerWord) * ( (double) STREAM_ARRAY_SIZE / 1024.0/1024./1024.));
        printf("Data is distributed across %d MPI ranks\n",numranks);
        printf("   Array size per MPI rank = %llu (elements)\n" , (unsigned long long) array_elements);
        printf("   Memory per array per MPI rank = %.1f MiB (= %.1f GiB).\n",
          BytesPerWord * ( (double) array_elements / 1024.0/1024.0),
          BytesPerWord * ( (double) array_elements / 1024.0/1024.0/1024.0));
        printf("   Total memory per MPI rank = %.1f MiB (= %.1f GiB).\n",
          (2.0 * BytesPerWord) * ( (double) array_elements / 1024.0/1024.),
          (2.0 * BytesPerWord) * ( (double) array_elements / 1024.0/1024./1024.));

        printf(HLINE);
        printf("The kernel will be executed %d times.\n", NTIMES);
        printf(" The *average* time for the kernel (excluding the first iteration)\n");
        printf(" will be used to compute the reported bandwidth.\n");

        #ifdef _OPENMP
            printf(HLINE);
            #pragma omp parallel
            {
                #pragma omp master
                {
                    k = omp_get_num_threads();
                    printf ("Number of Threads requested for each MPI rank = %i\n",k);
                }
            }
        #endif

        #ifdef _OPENMP
            k = 0;
            #pragma omp parallel
            #pragma omp atomic
                k++;
                printf ("Number of Threads counted for rank 0 = %i\n",k);
        #endif

    }

    /* --- SETUP --- initialize arrays and estimate precision of timer --- */

    #pragma omp parallel for
    for (j=0; j<array_elements; j++)
    {
        a[j] = 1.0;
        b[j] = 2.0;
    }

    // Rank 0 needs to allocate arrays and timing data from
    // all ranks for analysis and output.
    // Allocate and instantiate the arrays here -- after the primary arrays
    // have been instantiated -- so there is no possibility of having these
    // auxiliary arrays mess up the NUMA placement of the primary arrays.

    if (myrank == 0)
    {
        // There are 4*NTIMES timing values for each rank (always doubles)
        TimesByRank = (double *) malloc(NTIMES * sizeof(double) * numranks);
        if (TimesByRank == NULL)
        {
            printf("Ooops -- allocation of arrays to collect timing data on MPI rank 0 failed\n");
            MPI_Abort(MPI_COMM_WORLD, 3);
        }
        memset(TimesByRank,0,NTIMES*sizeof(double)*numranks);
    }

    // Simple check for granularity of the timer being used
    if (myrank == 0)
    {
        printf(HLINE);

        if  ( (quantum = checktick()) >= 1)
            printf("Your timer granularity/precision appears to be "
              "%d microseconds.\n", quantum);
        else
        {
            printf("Your timer granularity appears to be "
              "less than one microsecond.\n");
            quantum = 1;
        }
    }

    /* Get initial timing estimate to compare to timer granularity. */
    /* All ranks need to run this code since it changes the values in array a */
    t = MPI_Wtime();
    #pragma omp parallel for
    for (j = 0; j < array_elements; j++)
        a[j] = 2.0E0 * a[j];
    t = 1.0E6 * (MPI_Wtime() - t);

    if (myrank == 0)
    {
        printf("Each test below will take on the order"
          " of %d microseconds.\n", (int) t  );
        printf("   (= %d timer ticks)\n", (int) (t/quantum) );
        printf("Increase the size of the arrays if this shows that\n");
        printf("you are not getting at least 20 timer ticks per test.\n");

        printf("(WARNING -- The above is only a rough guideline.\n");
        printf("For best results, please be sure you know the\n");
        printf("precision of your system timer.)\n");
        printf(HLINE);
        #ifdef VERBOSE
            t1 = MPI_Wtime();
            printf("VERBOSE: total setup time for rank 0 = %f seconds\n",t1-t0);
            printf(HLINE);
        #endif
    }

    /*	--- MAIN LOOP --- repeat NTIMES times --- */

    // This code has more barriers and timing calls than are actually needed, but
    // this should not cause a problem for arrays that are large enough to satisfy
    // the STREAM run rules.

    for (k=0; k<NTIMES; k++)
    {
        // kernel : Copy
        t0 = MPI_Wtime();
        MPI_Barrier(MPI_COMM_WORLD);
        #pragma omp parallel
        {
            STREAM_copy_rw(a, b, &array_elements, &pause);
        }
        MPI_Barrier(MPI_COMM_WORLD);
        t1 = MPI_Wtime();
        times[k] = t1 - t0;
    }

    t0 = MPI_Wtime();

    /*	--- SUMMARY --- */

    // Because of the MPI_Barrier() calls, the timings from any thread are equally valid.

    // Gather all timing data to MPI rank 0
    MPI_Gather(times, NTIMES, MPI_DOUBLE, TimesByRank, NTIMES, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // Rank 0 processes all timing data
    if (myrank == 0)
    {
        // for each iteration and each kernel, collect the minimum time across all MPI ranks
        // and overwrite the rank 0 "times" variable with the minimum so the original post-
        // processing code can still be used.
        for (k=0; k<NTIMES; k++)
        {
            tmin = 1.0e36;
            for (i=0; i<numranks; i++)
            {
                // printf("DEBUG: Timing: iter %d, kernel %lu, rank %d, tmin %f, TbyRank %f\n",k,j,i,tmin,TimesByRank[NTIMES*i+j*NTIMES+k]);
                tmin = MIN(tmin, TimesByRank[NTIMES*i+k]);
            }
            // printf("DEBUG: Final Timing: iter %d, kernel %lu, final tmin %f\n",k,j,tmin);
            times[k] = tmin;
        }

        // Back to the original code, but now using the minimum global timing across all ranks
        for (k=1; k<NTIMES; k++) /* note -- skip first iteration */
        {
            avgtime = avgtime + times[k];
            mintime = MIN(mintime, times[k]);
            maxtime = MAX(maxtime, times[k]);
        }

        // note that "bytes" is the aggregate array size, so no "numranks" is needed here
        printf("\nMeasurements:\n");
        printf("                  Percentage of RD traffic    Pause      Avg  BW      Min  BW      Max  BW\n");
        avgtime = avgtime/(double)(NTIMES-1);

        printf("%s  %15d  %18d  %11.1f  %11.1f  %11.1f\n\n", label, rd_ratio,
          pause, 1.0E-06 * bytes/avgtime, 1.0E-06 * bytes/maxtime, 1.0E-06 * bytes/mintime);
        printf(HLINE);
    }


    free(a);
    free(b);
    if (myrank == 0)
    {
        free(TimesByRank);
    }

    MPI_Finalize();
    return(0);
}

# define	M	20

int checktick()
{
    int i, minDelta, Delta;
    double t1, t2, timesfound[M];

    /*  Collect a sequence of M unique time values from the system. */

    for (i = 0; i < M; i++)
    {
        t1 = MPI_Wtime();
        while( ((t2=MPI_Wtime()) - t1) < 1.0E-6 );
        timesfound[i] = t1 = t2;
    }

    /*
    * Determine the minimum difference between these M values.
    * This result will be our estimate (in microseconds) for the
    * clock granularity.
    */

    minDelta = 1000000;
    for (i = 1; i < M; i++)
    {
        Delta = (int)( 1.0E6 * (timesfound[i]-timesfound[i-1]));
        minDelta = MIN(minDelta, MAX(Delta,0));
    }

    return(minDelta);
}
