#!/bin/env python3
import os

from nmigen import *
from nmigen.back.verilog import convert
from nmigen.build import Platform

from c4m.nmigen.jtag import TAP

class DummyPlatform(Platform):
    resources = []
    connectors = []
    required_tools = ["yosys"]

    def toolchain_prepare(self, fragment, name, **kwargs):
        raise NotImplementedError

class Top(Elaboratable):
    def __init__(self, io_count):
        self.tap = TAP(io_count)
        self.core_i = Signal(io_count, name="top_corei")
        self.core_o = Signal(io_count, name="top_coreo")
        self.core_oe = Signal(io_count, name="top_coreoe")
        self.pad_i = Signal(io_count, name="top_padi")
        self.pad_o = Signal(io_count, name="top_pado")
        self.pad_oe = Signal(io_count, name="top_padoe")

    def elaborate(self, platform):
        m = Module()

        m.submodules.tap = self.tap

        m.d.comb += [
            self.core_i.eq(Cat(io.i for io in self.tap.core)),
            Cat(io.o for io in self.tap.core).eq(self.core_o),
            Cat(io.oe for io in self.tap.core).eq(self.core_oe),
            Cat(io.i for io in self.tap.pad).eq(self.pad_i),
            self.pad_o.eq(Cat(io.o for io in self.tap.pad)),
            self.pad_oe.eq(Cat(io.oe for io in self.tap.pad)),
        ]

        return m

top = Top(2)

p = DummyPlatform()

ports = [top.tap.bus.tck, top.tap.bus.tms, top.tap.bus.tdi, top.tap.bus.tdo,
         top.core_i, top.core_o, top.core_oe, top.pad_i, top.pad_o, top.pad_oe]
# for io in tap.core:
#     ports += [io.i, io.o, io.oe]
# for io in tap.pad:
#     ports += [io.i, io.o, io.oe]
top_code = convert(top, ports=ports, platform=p)
with open("code/top.v", "w") as f:
    f.write(top_code)

for filename, code in p.extra_files.items():
    with open("code"+ os.path.sep + filename, "w") as f:
        f.write(code)

    
