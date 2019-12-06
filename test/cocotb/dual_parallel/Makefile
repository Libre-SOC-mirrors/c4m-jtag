PWD=$(realpath .)
TOPDIR=$(realpath ../../..)
VHDLDIR=$(TOPDIR)/rtl/vhdl
VHDL_SOURCES = \
  $(VHDLDIR)/c4m_jtag_pkg.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_fsm.vhdl \
  $(VHDLDIR)/c4m_jtag_irblock.vhdl \
  $(VHDLDIR)/c4m_jtag_iocell.vhdl \
  $(VHDLDIR)/c4m_jtag_ioblock.vhdl \
  $(VHDLDIR)/c4m_jtag_idblock.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_controller.vhdl \
  $(PWD)/dual_parallel.vhdl
TOPLEVEL=dual_parallel
TOPLEVEL_LANG=vhdl
MODULE=test
SIM=ghdl
GPI_IMPL=vhpi
SIM_ARGS=--wave=test.ghw

COCOTBDIR=$(shell cocotb-path)

include $(COCOTBDIR)/makefiles/Makefile.inc
include $(COCOTBDIR)/makefiles/Makefile.sim
