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

from os import listdir, makedirs
from os.path import isfile, join
from shutil import rmtree
import multiprocessing, subprocess
from sys import argv
from random import seed, shuffle
from multiprocessing import cpu_count

CC = 'gcc'
CFLAGS = '-O0'

# Sizes of specific levels in memory hieararchy
l1 = 32//8
l2 = 256//8
l3 = 20*1024//8
mem = 4*1024*1024//8
#Set different sizes of generated files, sizes are in KB
#sizes = [i for i in range(0,l1,l1//8)][1:]+[i for i in range(l1,l2,(l2-l1)//16)]+[i for i in range(l2,l3,(l3-l2)//32)]+[i for i in range(l3,mem+1,(mem-l3)//64)]
#sizes = [i for i in range(l3,2*l3,l3//32)]
sizes = [524288]

ins = 5000000

sizes = [i*1024//64 for i in sizes]


def usage():
	print('Usage: ./generate.py <template_generator>.c <template_latency_bm>.c')
	exit(1)

def initialize_directories():
	# initialization of the working directories
	try:
		rmtree('gen/bin')
		rmtree('gen/data')
		rmtree('gen/src')
		rmtree('lat_bm/bin')
		rmtree('lat_bm/src')
	except:
		pass
	finally:
		makedirs('gen/bin')
		makedirs('gen/data')
		makedirs('gen/src')
		makedirs('lat_bm/bin')
		makedirs('lat_bm/src')

def compile(s):
	#Compile
	# Parallel using xargs
	proc = subprocess.Popen(['/usr/bin/xargs', '-n', '3', '-P', str(cpu_count()), CC, CFLAGS], stdin=subprocess.PIPE)
	proc.communicate(s.encode('utf-8'))
	proc.wait()


###############################################################################
# MAIN
###############################################################################

#Argument parsing

if len(argv) != 3:
	usage()

for i in range(1,len(argv)):
	if not isfile(argv[i]):
		print('Cannot locate ' + argv[i] + ', exiting.')
		exit(1)

sizes_kB = ''
for i in sizes:
	sizes_kB += str(i*64//1024)+'kB '


initialize_directories()

registers = ['rax','rbx', 'rdx', 'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15', 'rdi', 'rsi']

print('Generating benchmarks for sizes: '+sizes_kB)

for i in sizes:
	# Generators

	with open('gen/src/'+str((i*64)//1024).rjust(8,'0')+'-gen.c','w') as f:
		with open(argv[1],'r') as g:
			lines = g.readlines()
		for line in lines:
			if '#define N x' in line:
				f.write('#define N '+str(i)+'\n')
			elif 'fopen' in line:
				f.write('\tFILE *f = fopen("gen/data/'+str(i)+'.dat", "w");\n');
			elif 'Random walk file' in line:
				f.write('\tprintf("Random walk file generated at gen/data/'+str(i)+'.dat\\n");\n');
			else:
				f.write(line)
	# Benchmarks
	with open('lat_bm/src/'+str((i*64)//1024).rjust(8,'0')+'.c','w') as f:
		with open(argv[2],'r') as g:
			lines = g.readlines()
		for line in lines:
			if '#define N x' in line:
				f.write('#define N '+str(i)+'\n')
			elif 'fopen' in line:
				f.write('\tFILE *f = fopen("gen/data/'+str(i)+'.dat", "r");\n');
			elif 'Random walk file cannot be located' in line:
				f.write('\tprintf("Random walk file gen/data/'+str(i)+'.dat cannot be located.\\nExecute gen/bin/'+str((i*64)//1024).rjust(8,'0')+'-gen first.\\n");\n')
			elif 'register int i asm("ecx")' in line:
				f.write('\tregister int i asm("ecx") = '+str(int(ins/1000))+';\n');
			elif 'register struct line *next' in line:
				f.write('\tregister struct line *next asm("'+registers[0]+'");\n');
			elif 'next = array->next;' in line:
				f.write('\tnext = array[0].next;\n')
			elif "mov (%rbx,%rdx), %rdx;" in line:
				for i in range(1000):
					f.write('\t\t\t"mov (%rbx,%'+registers[0]+'), %'+registers[0]+';"\n');
			else:
				f.write(line)

print('Done generating benchmarks.')

# Done generating, moving to compile
onlyfiles = sorted([ f for f in listdir('gen/src') if isfile(join('gen/src',f)) ])

print('Compiling generator files...')

for f in onlyfiles:
	s='gen/src/'+f+' -o gen/bin/'+f[:-2]
	print('\t' + CC + ' ' + CFLAGS + ' ' + s)
	compile(s)

print('Done compiling.')

onlyfiles = sorted([ f for f in listdir('lat_bm/src') if isfile(join('lat_bm/src',f)) ])

print('Compiling benchmark files...')

for f in onlyfiles:
	s='lat_bm/src/'+f+' -o lat_bm/bin/'+f[:-2]
	print('\t' + CC + ' ' + CFLAGS + ' ' + s)
	compile(s)

print('Done compiling.')

