#!/bin/sh
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_pkg.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_tap_fsm.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_irblock.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_idblock.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_iocell.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_ioblock.vhdl
ghdl -a --std=08 ../../rtl/vhdl/c4m_jtag_tap_controller.vhdl
ghdl -a --std=08 ../../bench/vhdl/idcode.vhdl
ghdl -r --std=08 bench_idcode --wave=bench_idcode.ghw
