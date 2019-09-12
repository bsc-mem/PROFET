CC = icc
MPICC = mpicc
CFLAGS = -O3 -Wall -march=native

SRCDIR=src
BUILDDIR=build
BINDIR=bin

PRG_SUFFIX=.x

all: $(BINDIR)/stream_mpi$(PRG_SUFFIX)

$(BUILDDIR)/mysecond.o: $(SRCDIR)/mysecond.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILDDIR)/nop.o: $(SRCDIR)/nop.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILDDIR)/utils.o: $(SRCDIR)/utils.c
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILDDIR)/stream_mpi_c.o: $(SRCDIR)/stream_mpi.c
	$(MPICC) $(CFLAGS) -c $< -o $@
	
$(BINDIR)/stream_mpi$(PRG_SUFFIX): $(BUILDDIR)/mysecond.o $(BUILDDIR)/nop.o $(BUILDDIR)/utils.o $(BUILDDIR)/stream_mpi_c.o
	$(MPICC) $(CCFLAGS) $^ -o $@

clean:
	rm -f $(BUILDDIR)/*.o $(BINDIR)/*
