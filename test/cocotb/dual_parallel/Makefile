CURDIR=$(realpath .)
TOPDIR=$(realpath ../../..)

ifeq ($(PYTHONPATH),)
  PYTHONPATH := $(TOPDIR)
else
  PYTHONPATH := $(TOPDIR):$(PYTHONPATH)
endif
export PYTHONPATH

VHDLDIR=$(TOPDIR)/c4m/vhdl/jtag
VHDL_SOURCES = \
  $(VHDLDIR)/c4m_jtag_pkg.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_fsm.vhdl \
  $(VHDLDIR)/c4m_jtag_irblock.vhdl \
  $(VHDLDIR)/c4m_jtag_iocell.vhdl \
  $(VHDLDIR)/c4m_jtag_ioblock.vhdl \
  $(VHDLDIR)/c4m_jtag_idblock.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_controller.vhdl \
  $(CURDIR)/dual_parallel.vhdl
TOPLEVEL=dual_parallel
TOPLEVEL_LANG=vhdl
MODULE=test
SIM=ghdl
GPI_IMPL=vhpi
SIM_ARGS=--wave=test.ghw

COCOTBMAKEFILESDIR=$(shell cocotb-config --makefiles)

include $(COCOTBMAKEFILESDIR)/Makefile.inc
include $(COCOTBMAKEFILESDIR)/Makefile.sim
