CURDIR = $(realpath .)
TOPDIR = $(realpath ../../../..)

NMIGENDIR := $(TOPDIR)/c4m/nmigen/jtag

ifeq ($(PYTHONPATH),)
  PYTHONPATH := $(TOPDIR)
else
  PYTHONPATH := $(TOPDIR):$(PYTHONPATH)
endif
export PYTHONPATH

OUTPUTS := top.v
INPUTS := $(addprefix $(NMIGENDIR)/,bus.py tap.py)
SCRIPT := ./generate.py

.PHONY: all
all: $(OUTPUTS)

# We just test if top verilog file can be generated
top.v: $(SCRIPT) $(INPUTS)
	@echo "Regenerating"
	@$(SCRIPT)

.PHONY: clean
clean:
	@rm -f $(OUTPUTS)
