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

cc = 'gcc'
cflags = '-mcmodel=large'

# Sizes of specific levels in memory hieararchy
l1 = 32//8
l2 = 256//8
l3 = 20*1024//8
mem = 4*1024*1024//8

#Set different sizes of generated files, sizes are in KB
#sizes = [i for i in range(0,l1,l1//8)][1:]+[i for i in range(l1,l2,(l2-l1)//16)]+[i for i in range(l2,l3,(l3-l2)//32)]+[i for i in range(l3,mem+1,(mem-l3)//64)]
#sizes = [i for i in range(l3,2*l3,l3//32)]
sizes = [524288]

def initialize_directories():
	# initialization of the working directories
	try:
		rmtree('gen/bin')
		rmtree('gen/data')
		rmtree('gen/src')
	except:
		pass
	finally:
		makedirs('gen/bin')
		makedirs('gen/data')
		makedirs('gen/src')

sizes = [i*1024//64 for i in sizes]

initialize_directories()

sizes_kB = ''
for i in sizes:
	sizes_kB += str(i*64//1024)+'kB '

if len(sizes) > 1:
	print('Generating files for sizes: '+sizes_kB)
else:
	print('Generating file for size: '+sizes_kB)

for i in sizes:
	# Generator

	with open('gen/src/'+str((i*64)//1024).rjust(8,'0')+'-gen.c','w') as f:
		with open('generator.c','r') as g:
			lines = g.readlines()
			for line in lines:
				if '#define N x' in line:
					f.write('#define N '+str(i)+'\n')
				elif 'fopen' in line:
					f.write('\tFILE *f = fopen("gen/data/'+str(i)+'.dat", "w");\n');
				else:
					f.write(line)

# Done generating, moving to compile
onlyfiles = sorted([ f for f in listdir('gen/src') if isfile(join('gen/src',f)) ])

# Parallel using xargs
s = ''
for f in onlyfiles:
	s+='gen/src/'+f+' -o gen/bin/'+f[:-2]+' '

print(cc+' '+cflags+' '+s)

proc = subprocess.Popen(['/usr/bin/xargs', '-n', '3', '-P', str(cpu_count()), cc, cflags], stdin=subprocess.PIPE)
proc.communicate(s.encode('utf-8'))
proc.wait()

file_names = ''

for f in onlyfiles:
	file_names += 'gen/bin/'+f[:-2] + ' '

if len(sizes) > 1:
	print('Random walk files '+file_names+'generated.')
else:
	print('Random walk file '+file_names+'generated.')
