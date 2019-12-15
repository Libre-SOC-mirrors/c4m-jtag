#!/bin/sh
vhdldir=`realpath ../../../../c4m/vhdl/jtag`
opts=--std=08
ghdl -a $opts $vhdldir/c4m_jtag_pkg.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_tap_fsm.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_irblock.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_idblock.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_iocell.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_ioblock.vhdl
ghdl -a $opts $vhdldir/c4m_jtag_tap_controller.vhdl
ghdl -a $opts ./idcode.vhdl
ghdl -r $opts bench_idcode --wave=bench_idcode.ghw
