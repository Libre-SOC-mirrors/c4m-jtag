#!/bin/env python3
import os

from nmigen import *
from nmigen.back.verilog import convert
from nmigen.build import Platform

from c4m.nmigen.jtag import TAP, IOType, IOConn

class DummyPlatform(Platform):
    resources = []
    connectors = []
    required_tools = ["yosys"]

    def toolchain_prepare(self, fragment, name, **kwargs):
        raise NotImplementedError

class Top(Elaboratable):
    iotypes = (IOType.In, IOType.Out, IOType.TriOut, IOType.InTriOut)

    def __init__(self, io_count):
        self.tap = tap = TAP()
        self.ios = [tap.add_io(iotype=iotype) for iotype in self.iotypes]

        self.sr = tap.add_shiftreg(ircode=3, length=3)

        self.wb = tap.add_wishbone(ircodes=[4, 5, 6], address_width=16, data_width=8)

    def elaborate(self, platform):
        m = Module()

        m.submodules.tap = self.tap

        m.d.comb += self.sr.i.eq(self.sr.o)

        return m

top = Top(2)

p = DummyPlatform()

ports = [top.tap.bus.tck, top.tap.bus.tms, top.tap.bus.tdi, top.tap.bus.tdo]
for conn in top.ios:
    for sig in ("i", "o", "oe"):
        try:
            ports += [getattr(conn.core, sig), getattr(conn.pad, sig)]
        except:
            pass

top_code = convert(top, ports=ports, platform=p)
with open("code/top.v", "w") as f:
    f.write(top_code)

for filename, code in p.extra_files.items():
    with open("code"+ os.path.sep + filename, "w") as f:
        f.write(code)
