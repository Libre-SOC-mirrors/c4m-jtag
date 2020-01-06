CURDIR=$(realpath .)
TOPDIR=$(realpath ../../../..)

ifeq ($(PYTHONPATH),)
  PYTHONPATH := $(TOPDIR)
else
  PYTHONPATH := $(TOPDIR):$(PYTHONPATH)
endif
export PYTHONPATH

TOPLEVEL := top

CODEDIR := $(CURDIR)/code
TOPFILE := $(CODEDIR)/$(TOPLEVEL).v
TOPVCD := $(CURDIR)/$(TOPLEVEL).vcd

#
# COCOTB
#
VHDL_SOURCES = \
#VHDL_SOURCES end
VERILOG_SOURCES = \
  $(TOPFILE) \
#VERILOG_SOURCES end
ALL_SOURCES := $(VHDL_SOURCES) $(VERILOG_SOURCES)
TOPLEVEL_LANG := verilog
MODULE := test
SIM := modelsim
ARCH := i686
VCOM_ARGS := -2008
WAVES := 1

COCOTBMAKEFILESDIR=$(shell cocotb-config --makefiles)

# Add top target to convert output to vcd
top: $(TOPVCD)

include $(COCOTBMAKEFILESDIR)/Makefile.inc
include $(COCOTBMAKEFILESDIR)/Makefile.sim


#
# Code generation
#
.PHONY: rtl
rtl: $(ALL_SOURCES)
$(ALL_SOURCES): generate_once

GENERATE := ./generate.py
TOPDEPS := \
  $(TOPDIR)/c4m/nmigen/jtag/tap.py \
#TOPDEPS end

.INTERMEDIATE: generate_once
generate_once: $(GENERATE) $(TOPDEPS) | $(CODEDIR)/jtag
	@echo "Generating RTL"
	@$(GENERATE)

$(CODEDIR)/jtag:
	@mkdir -p $@


#
# Convert waveform
#
$(TOPVCD): sim
	wlf2vcd -o $@ sim_build/vsim.wlf


.PHONY: clean
clean::
	@rm -fr code $(TOPVCD) __pycache__
