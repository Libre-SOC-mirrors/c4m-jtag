#!/bin/env python3
import os

from nmigen import *
from nmigen.build import *
from nmigen.lib.io import *
from nmigen.tracer import get_var_name

from c4m_repo.nmigen.lib import Wishbone

__all__ = [
    "TAP",
]


class ShiftReg(Elaboratable):
    def __init__(self, ircodes, length, domain):
        # The sr record will be returned to user code
        self.sr = Record([("i", length), ("o", length), ("oe", len(ircodes)), ("ack", 1)])
        # The next attributes are for JTAG class usage only
        self.ir = None # made None as width is not known yet
        self.tdi = Signal()
        self.tdo = Signal()
        self.tdo_en = Signal()
        self.capture = Signal()
        self.shift = Signal()
        self.update = Signal()
        self.jtag_cd = None # The JTAG clock domain

        ##

        self._ircodes = ircodes
        self._domain = domain

    def elaborate(self, platform):
        length = len(self.sr.o)
        domain = self._domain

        m = Module()

        m.domains.jtag = self.jtag_cd

        sr_jtag = Signal(length)

        assert isinstance(self.ir, Signal)
        isir = Signal(len(self._ircodes))
        capture = Signal()
        shift = Signal()
        update = Signal()
        m.d.comb += [
            isir.eq(Cat(self.ir == ircode for ircode in self._ircodes)),
            capture.eq((isir != 0) & self.capture),
            shift.eq((isir != 0) & self.shift),
            update.eq((isir != 0) & self.update),
        ]

        # On update set o, oe and wait for ack
        # update signal is on JTAG clockdomain, latch it
        update_core = Signal()
        m.d[domain] += update_core.eq(update) # This is CDC from JTAG domain to given domain
        with m.FSM(domain=domain):
            with m.State("IDLE"):
                m.d.comb += self.sr.oe.eq(0)
                with m.If(update_core):
                    # Latch sr_jtag cross domain but it should be stable due to latching of update_core
                    m.d[domain] += self.sr.o.eq(sr_jtag)
                    # Wait one cycle to raise oe so sr.o has one more cycle to stabilize
                    m.next = "WAIT4ACK"
            with m.State("WAIT4ACK"):
                m.d.comb += self.sr.oe.eq(isir)
                with m.If(self.sr.ack):
                    m.next = "WAIT4END"
            with m.State("WAIT4END"):
                m.d.comb += self.sr.oe.eq(0)
                with m.If(~update_core):
                    m.next = "IDLE"

        m.d.comb += [
            self.tdo.eq(sr_jtag[0]),
            self.tdo_en.eq(shift),
        ]

        with m.If(shift):
            m.d.jtag += sr_jtag.eq(Cat(sr_jtag[1:], self.tdi))
        with m.If(capture):
            m.d.jtag += sr_jtag.eq(self.sr.i)

        return m

class JTAGWishbone(Elaboratable):
    def __init__(self, sr_addr, sr_data, wb, domain):
        self._sr_addr = sr_addr
        self._sr_data = sr_data
        self._wb = wb
        self._domain = domain

        # To be set by JTAG
        self._ir = None

    def elaborate(self, platform):
        sr_addr = self._sr_addr
        sr_data = self._sr_data
        wb = self._wb
        domain = self._domain
        ir = self._ir

        m = Module()

        if hasattr(wb, "sel"):
            # Always selected
            m.d.comb += [s.eq(1) for s in wb.sel]

        # Immediately ack oe
        m.d[domain] += [
            sr_addr.ack.eq(sr_addr.oe),
            sr_data.ack.eq(sr_data.oe != 0),
        ]

        with m.FSM(domain=domain) as fsm:
            with m.State("IDLE"):
                m.d.comb += [
                    wb.cyc.eq(0),
                    wb.stb.eq(0),
                    wb.we.eq(0),
                ]
                with m.If(sr_addr.oe): # WBADDR code
                    m.d[domain] += wb.addr.eq(sr_addr.o)
                    m.next = "READ"
                with m.If(sr_data.oe[0]): # WBREAD code
                    m.d[domain] += wb.addr.eq(wb.addr + 1)
                    m.next = "READ"
                with m.If(sr_data.oe[1]): # WBWRITE code
                    m.d[domain] += wb.dat_w.eq(sr_data.o)
                    m.next = "WRITEREAD"
            with m.State("READ"):
                m.d.comb += [
                    wb.cyc.eq(1),
                    wb.stb.eq(1),
                    wb.we.eq(0),
                ]
                with m.If(~wb.stall):
                    m.next = "READACK"
            with m.State("READACK"):
                m.d.comb += [
                    wb.cyc.eq(1),
                    wb.stb.eq(0),
                    wb.we.eq(0),
                ]
                with m.If(wb.ack):
                    m.d[domain] += sr_data.i.eq(wb.dat_r)
                    m.next = "IDLE"
            with m.State("WRITEREAD"):
                m.d.comb += [
                    wb.cyc.eq(1),
                    wb.stb.eq(1),
                    wb.we.eq(1),
                ]
                with m.If(~wb.stall):
                    m.next = "WRITEREADACK"
            with m.State("WRITEREADACK"):
                m.d.comb += [
                    wb.cyc.eq(1),
                    wb.stb.eq(0),
                    wb.we.eq(0),
                ]
                with m.If(wb.ack):
                    m.d[domain] += wb.addr.eq(wb.addr + 1)
                    m.next = "READ"

        return m


class TAP(Elaboratable):
    #TODO: Document TAP
    @staticmethod
    def _add_files(platform, prefix):
        d = os.path.realpath("{dir}{sep}{par}{sep}{par}{sep}vhdl{sep}jtag".format(
            dir=os.path.dirname(__file__), sep=os.path.sep, par=os.path.pardir
        )) + os.path.sep
        for fname in [
            "c4m_jtag_pkg.vhdl",
            "c4m_jtag_idblock.vhdl",
            "c4m_jtag_iocell.vhdl",
            "c4m_jtag_ioblock.vhdl",
            "c4m_jtag_irblock.vhdl",
            "c4m_jtag_tap_fsm.vhdl",
            "c4m_jtag_tap_controller.vhdl",
        ]:
            f = open(d + fname, "r")
            platform.add_file(prefix + fname, f)
            f.close()


    def __init__(self, io_count, *, ir_width=None, manufacturer_id=Const(0b10001111111, 11),
                 part_number=Const(1, 16), version=Const(0, 4)
    ):
        assert(isinstance(io_count, int) and io_count > 0)
        assert((ir_width is None) or (isinstance(ir_width, int) and ir_width >= 2))
        assert(len(version) == 4)

        # TODO: Handle IOs with different directions
        self.tck  = Signal()
        self.tms  = Signal()
        self.tdo  = Signal()
        self.tdi  = Signal()
        self.core = Array(Pin(1, "io") for _ in range(io_count)) # Signals to use for core
        self.pad  = Array(Pin(1, "io") for _ in range(io_count)) # Signals going to IO pads

        self.jtag_cd = ClockDomain(name="jtag", local=True) # Own clock domain using TCK as clock signal

        ##

        self._io_count = io_count
        self._ir_width = ir_width
        self._manufacturer_id = manufacturer_id
        self._part_number = part_number
        self._version = version

        self._ircodes = [0, 1, 2] # Already taken codes, all ones added at the end
        self._srs = []

        self._wbs = []

    def elaborate(self, platform):
        TAP._add_files(platform, "jtag" + os.path.sep)

        m = Module()

        tdo_jtag = Signal()
        reset = Signal()
        capture = Signal()
        shift = Signal()
        update = Signal()


        ir_max = max(self._ircodes) + 1 # One extra code needed with all ones
        ir_width = len("{:b}".format(ir_max))
        if self._ir_width is not None:
            assert self._ir_width >= ir_width, "Specified JTAG IR width not big enough for allocated shiift registers"
            ir_width = self._ir_width
        ir = Signal(ir_width)

        core_i = Cat(pin.i for pin in self.core)
        core_o = Cat(pin.o for pin in self.core)
        core_oe = Cat(pin.oe for pin in self.core)
        pad_i = Cat(pin.i for pin in self.pad)
        pad_o = Cat(pin.o for pin in self.pad)
        pad_oe = Cat(pin.oe for pin in self.pad)

        params = {
            "p_IOS": self._io_count,
            "p_IR_WIDTH": ir_width,
            "p_MANUFACTURER": self._manufacturer_id,
            "p_PART_NUMBER": self._part_number,
            "p_VERSION": self._version,
            "i_TCK": self.tck,
            "i_TMS": self.tms,
            "i_TDI": self.tdi,
            "o_TDO": tdo_jtag,
            "i_TRST_N": Const(1),
            "o_RESET": reset,
            "o_DRCAPTURE": capture,
            "o_DRSHIFT": shift,
            "o_DRUPDATE": update,
            "o_IR": ir,
            "o_CORE_IN": core_i,
            "i_CORE_OUT": core_o,
            "i_CORE_EN": core_oe,
            "i_PAD_IN": pad_i,
            "o_PAD_OUT": pad_o,
            "o_PAD_EN": pad_oe,
        }
        m.submodules.tap = Instance("c4m_jtag_tap_controller", **params)

        m.d.comb += [
            self.jtag_cd.clk.eq(self.tck),
            self.jtag_cd.rst.eq(reset),
        ]

        for i, sr in enumerate(self._srs):
            m.submodules["sr{}".format(i)] = sr
            sr.ir = ir
            m.d.comb += [
                sr.tdi.eq(self.tdi),
                sr.capture.eq(capture),
                sr.shift.eq(shift),
                sr.update.eq(update),
            ]

        if len(self._srs) > 0:
            first = True
            for sr in self._srs:
                if first:
                    first = False
                    with m.If(sr.tdo_en):
                        m.d.comb += self.tdo.eq(sr.tdo)
                else:
                    with m.Elif(sr.tdo_en):
                        m.d.comb += self.tdo.eq(sr.tdo)
            with m.Else():
                m.d.comb += self.tdo.eq(tdo_jtag)
        else:
            m.d.comb += self.tdo.eq(tdo_jtag)

        for i, wb in enumerate(self._wbs):
            m.submodules["wb{}".format(i)] = wb
            wb._ir = ir

        return m


    def add_shiftreg(self, ircode, length, domain="sync"):
        """Add a shift register to the JTAG interface

        Parameters:
        - ircode: code(s) for the IR; int or sequence of ints. In the latter case this
          shiftreg is shared between different IR codes.
        - length: the length of the shift register
        - domain: the domain on which the signal will be used"""

        try:
            ir_it = iter(ircode)
            ircodes = ircode
        except TypeError:
            ir_it = ircodes = (ircode,)
        for _ircode in ir_it:
            assert(isinstance(_ircode, int) and _ircode > 0 and _ircode not in self._ircodes)

        sr = ShiftReg(ircodes, length, domain)
        sr.jtag_cd = self.jtag_cd
        self._ircodes.extend(ircodes)
        self._srs.append(sr)

        return sr.sr


    def add_wishbone(self, ircodes, address_width, data_width, sel_width=None, domain="sync"):
        """Add a wishbone interface

        Parameters:
        - ircodes: sequence of three integer for the JTAG IR codes;
          they represent resp. WBADDR, WBREAD and WBREADWRITE. First code
          has a shift register of length 'address_width', the two other codes
          share a shift register of length data_width.
        - address_width: width of the address
        - data_width: width of the data"""

        assert len(ircodes) == 3

        sr_addr = self.add_shiftreg(ircodes[0], address_width, domain=domain)
        sr_data = self.add_shiftreg(ircodes[1:], data_width, domain=domain)

        wb = Wishbone(data_width=data_width, address_width=address_width, sel_width=sel_width, master=True)

        self._wbs.append(JTAGWishbone(sr_addr, sr_data, wb, domain))

        return wb
