#!/usr/bin/env python3
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


tap = TAP(ir_width=2)
f = open("top.v", "w")
f.write(convert(tap, platform=DummyPlatform()))
f.close()

