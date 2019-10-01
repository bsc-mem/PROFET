CC = gcc
#CC = icc
MPICC = mpicc
CFLAGS = -march=native -fopenmp
LDFLAGS = -pthread -lrt

SRCDIR=src
BUILDDIR=build
BINDIR=bin

PRG_SUFFIX=.x

all: init $(BINDIR)/stream_mpi$(PRG_SUFFIX)

init:
	mkdir -p $(BUILDDIR)
	mkdir -p $(BINDIR)

$(BUILDDIR)/mysecond.o: $(SRCDIR)/mysecond.c
	$(CC) $(CFLAGS) -O3 -c $< -o $@

$(BUILDDIR)/nop.o: $(SRCDIR)/nop.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILDDIR)/utils.o: $(SRCDIR)/utils.c
	$(CC) $(CFLAGS) -O0 -c $< -o $@

$(BUILDDIR)/stream_mpi_c.o: $(SRCDIR)/stream_mpi.c
	$(MPICC) $(CFLAGS) -O3 -c $< -o $@
	
$(BINDIR)/stream_mpi$(PRG_SUFFIX): $(BUILDDIR)/mysecond.o $(BUILDDIR)/nop.o $(BUILDDIR)/utils.o $(BUILDDIR)/stream_mpi_c.o
	$(MPICC) $(CFLAGS) -O3 $(LDFLAGS) $^ -o $@

clean:
	rm -f $(BUILDDIR)/*.o $(BINDIR)/*

