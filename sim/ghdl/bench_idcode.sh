#!/bin/sh
ghdl -i ../../rtl/vhdl/c4m_jtag_*.vhdl
ghdl -i ../../bench/vhdl/idcode.vhdl
ghdl -m bench_idcode
./bench_idcode --wave=bench_idcode.ghw
