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

#define N x
#include <stdlib.h>
#include <stdio.h>

struct line{
	struct line *next;
	int pad[14];
};

struct line *array;
int seq[N-1];
int res[N];


//Taken from: http://stackoverflow.com/questions/6127503/shuffle-array-in-c
/* Arrange the N elements of ARRAY in random order.
   Only effective if N is much smaller than RAND_MAX;
   if this may not be the case, use a better random
   number generator. */
void shuffle(int *array, size_t n) {
	srand(0);
    if (n > 1) 
    {
        size_t i;
        for (i = 0; i < n - 1; i++) 
        {
          size_t j = i + rand() / (RAND_MAX / (n - i) + 1);
          int t = array[j];
          array[j] = array[i];
          array[i] = t;
        }
    }
}

void walk_generator(){
	int j;
	// Init the position array
	for(j=1;j<N;j++){
		seq[j-1] = j;
	}	
	
	shuffle(seq,N-1);
		
	res[0] = seq[0];
	int n = res[0];
	for(j=0;j<N-1;j++){
		res[n] = seq[j];
		n = res[n];
	}
	
	for(j=0;j<N;j++){
		array[j].next = (struct line *) (long) (res[j] * 64);
	}
}

int main(int argc, char *argv[]) {
	int r, array_bytes;
        array_bytes = N * sizeof(struct line);
        r = posix_memalign((void **)&array, 64, array_bytes);
        if (r != 0) {
                printf("Allocation of array failed, return code is %d\n",r);
                exit(1);
        }
	walk_generator();
	FILE *f = fopen("array.dat", "w");
	fwrite(array, sizeof(*array), N, f);
	fclose(f);
	free(array);
	printf("Random walk file generated.\n");
	return 0;
}

