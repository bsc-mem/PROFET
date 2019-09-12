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

struct line array[N];

int main(int argc, char *argv[]) {
	printf("\n");
	FILE *f = fopen("array.dat","r");
	fread(array,sizeof(array),1,f);
	fclose(f);
	//printf("%p\n",array);
	register int i asm("ecx") = 5000;
	register struct line *next asm("rdx");
	next = array->next;
	__asm__ __volatile__ (
		"start_loop:"
			"mov (%rdx), %rdx;"
		"dec %ecx;"
		"jnz start_loop;"
	);
	printf("Done walking the file!\n");
	exit(0);
}
