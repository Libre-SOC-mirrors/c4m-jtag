CURDIR=$(realpath .)
TOPDIR=$(realpath ../../../..)

VHDLDIR=$(TOPDIR)/c4m/vhdl/jtag
VHDL_SOURCES = \
  $(VHDLDIR)/c4m_jtag_pkg.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_fsm.vhdl \
  $(VHDLDIR)/c4m_jtag_irblock.vhdl \
  $(VHDLDIR)/c4m_jtag_iocell.vhdl \
  $(VHDLDIR)/c4m_jtag_ioblock.vhdl \
  $(VHDLDIR)/c4m_jtag_idblock.vhdl \
  $(VHDLDIR)/c4m_jtag_tap_controller.vhdl \
  $(CURDIR)/ioblock.vhdl \
#end VHDL_SOURCES
TOPLEVEL=ioblock
TOPLEVEL_LANG=vhdl
MODULE=test
SIM=ghdl
GPI_IMPL=vhpi
GHDL_ARGS=--std=08
SIM_ARGS=--wave=test.ghw

COCOTBMAKEFILESDIR=$(shell cocotb-config --makefiles)

include $(COCOTBMAKEFILESDIR)/Makefile.inc
include $(COCOTBMAKEFILESDIR)/Makefile.sim
