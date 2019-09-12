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

from os import listdir, mkdir, makedirs
from os.path import isfile, join
from shutil import rmtree
import multiprocessing, subprocess
from sys import argv, exit
from random import seed, shuffle
from multiprocessing import cpu_count
import argparse

cc = 'gcc'
cflags = '-mcmodel=large'

#This is the sizes array I use for my test
l1 = 32
l2 = 256
l3 = 20*1024
mem = 4*1024*1024
#Change this line to change the sizes
#sizes = [i for i in range(0,l1,l1//8)][1:]+[i for i in range(l1,l2,(l2-l1)//16)]+[i for i in range(l2,l3,(l3-l2)//32)]+[i for i in range(l3,mem+1,(mem-l3)//64)]
sizes = [524288]
ins = 5000

def usage():
	print('Usage: ./latencyasm.py <template>.c ...')
	exit(1)

def initialize_directories(templates):
        #Parent directories
        for t in templates:
                try:
                        rmtree(t[:-2])
                except:
                        pass #Directory didn't exist in the first place, do nothing
                finally:
                        path = t[:-2]
                        #initialization of the working directory
                        makedirs(join(path,'src'))
                        makedirs(join(path,'bin'))

def benchmark(i, template):
	registers = ['rax','rbx', 'rdx', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15', 'rdi', 'rsi']
	#Benchmark
	with open(template[:-2] + '/src/'+str((i*64)//1024).rjust(8,'0')+'.c','w') as f:
		g = open(template) #Check that template exists
		lines = g.readlines()
		for line in lines:
			if '#define N x' in line:
				f.write('#define N '+str(i)+'\n')
			elif 'fopen' in line:
				f.write('\tFILE *f = fopen("gen/data/'+str(i)+'.dat", "r");\n');
			elif 'register int i asm("ecx")' in line:
				f.write('\tregister int i asm("ecx") = '+str(ins)+';\n');
			elif 'register struct line *next' in line:
				f.write('\tregister struct line *next asm("'+registers[0]+'");\n');
			elif 'next = array->next;' in line:
				f.write('\tnext = array[0].next;\n')
			elif "mov (%rdx), %rdx;" in line:
				for i in range(1000):
					f.write('\t\t\t"mov (%'+registers[0]+'), %'+registers[0]+';"\n');
			else:
				f.write(line)

def compile(s):
	#Compile
	proc = subprocess.Popen(['/usr/bin/xargs', '-n', '3', '-P', str(cpu_count()), cc, cflags], stdin=subprocess.PIPE)
	proc.communicate(s.encode('utf-8'))
	proc.wait()

###############################################################################
# MAIN
###############################################################################

#Argument parsing

if len(argv) != 2:
	usage()

if not isfile(argv[1]):
	print('Cannot locate '+argv[1])
	exit(1)

sizes = [i*1024//64 for i in sizes]
#sizes = sizes[:1]

initialize_directories(argv[1:])

sizes_kB = ''
for i in sizes:
        sizes_kB += str(i*64//1024)+'kB '

if len(sizes) > 1:
        print('Generating benchmarks for sizes: '+sizes_kB)
else:
        print('Generating benchmark for size: '+sizes_kB)

#Generate benchmarks
for t in argv[1:]:
	for i in sizes:
		benchmark(i,t)

#Done, lets compile
for t in argv[1:]:
	template = t[:-2]
	onlyfiles = sorted([ f for f in listdir(template+'/src') if isfile(join(template+'/src',f)) ])

	#Parallel using xargs
	s = ''
	for f in onlyfiles:
		s+=template+'/src/'+f+' -o '+template+'/bin/'+f[:-2]+' '

	print(cc+' '+cflags+' '+s)

	#Done, let's compile
	compile(s)

file_names = ''

for f in onlyfiles:
        file_names += 'lat_bm/bin/'+f[:-2] + ' '

if len(sizes) > 1:
        print('Benchmarks '+file_names+'generated.')
else:
        print('Benchmark '+file_names+'generated.')
