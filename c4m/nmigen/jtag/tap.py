#!/bin/env python3
import os, textwrap

from nmigen import *
from nmigen.build import *
from nmigen.lib.io import *
from nmigen.hdl.rec import Direction
from nmigen.tracer import get_var_name

from nmigen_soc.wishbone import Interface as WishboneInterface

from .bus import Interface

__all__ = [
    "TAP", "ShiftReg",
]


class ShiftReg(Record):
    """Object with interface for extra shift registers on a TAP.

    Parameters
    ----------
    sr_length : int
    cmds : int, default=1
        The number of corresponding JTAG instructions

    This object is normally only allocated and returned from ``TAP.add_shiftreg``
    It is a Record subclass.

    Attributes
    ----------
    i: length=sr_length, FANIN
        The input data sampled during capture state of the TAP
    ie: length=cmds, FANOUT
        Indicates that data is to be sampled by the JTAG TAP and
        should be held stable. The bit indicates the corresponding
        instruction for which data is asked.
        This signal is kept high for a whole JTAG TAP clock cycle
        and may thus be kept higher for more than one clock cycle
        on the domain where ShiftReg is used.
        The JTAG protocol does not allow insertion of wait states
        so data need to be provided before ie goes down. The speed
        of the response will determine the max. frequency for the
        JTAG interface.
    o: length=sr_length, FANOUT
        The value of the shift register.
    oe: length=cmds, FANOUT
        Indicates that output needs to be sampled downstream because
        JTAG TAP in in the Update state. The bit indicated the corresponding
        instruction. The bit is only kept high for one clock cycle.
    """
    def __init__(self, *, sr_length, cmds=1, name=None, src_loc_at=0):
        layout = [
            ("i", sr_length, Direction.FANIN),
            ("ie", cmds, Direction.FANOUT),
            ("o", sr_length, Direction.FANOUT),
            ("oe", cmds, Direction.FANOUT),
        ]
        super().__init__(layout, name=name, src_loc_at=src_loc_at+1)


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

    _controller_templ = textwrap.dedent(r"""
    library ieee;
    use ieee.std_logic_1164.ALL;
    
    use work.c4m_jtag.ALL;
    
    entity {name} is
      port (
        -- The TAP signals
        TCK:        in std_logic;
        TMS:        in std_logic;
        TDI:        in std_logic;
        TDO:        out std_logic;
        TRST_N:     in std_logic;
    
        -- The FSM state indicators
        RESET:      out std_logic;
        CAPTURE:    out std_logic;
        SHIFT:      out std_logic;
        UPDATE:     out std_logic;
    
        -- The Instruction Register
        IR:         out std_logic_vector({ir_width}-1 downto 0);
    
        -- The I/O access ports
        CORE_IN:    out std_logic_vector({ios}-1 downto 0);
        CORE_EN:    in std_logic_vector({ios}-1 downto 0);
        CORE_OUT:   in std_logic_vector({ios}-1 downto 0);
    
        -- The pad connections
        PAD_IN:     in std_logic_vector({ios}-1 downto 0);
        PAD_EN:     out std_logic_vector({ios}-1 downto 0);
        PAD_OUT:    out std_logic_vector({ios}-1 downto 0)
      );
    end {name};
    
    architecture rtl of {name} is
    begin
      jtag : c4m_jtag_tap_controller
        generic map(
          DEBUG => FALSE,
          IR_WIDTH => {ir_width},
          IOS => {ios},
          MANUFACTURER => "{manufacturer:011b}",
          PART_NUMBER => "{part:016b}",
          VERSION => "{version:04b}"
        )
        port map(
          TCK => TCK,
          TMS => TMS,
          TDI => TDI,
          TDO => TDO,
          TRST_N => TRST_N,
          RESET => RESET,
          CAPTURE => CAPTURE,
          SHIFT => SHIFT,
          UPDATE => UPDATE,
          IR => IR,
          CORE_IN => CORE_IN,
          CORE_EN => CORE_EN,
          CORE_OUT => CORE_OUT,
          PAD_IN => PAD_IN,
          PAD_EN => PAD_EN,
          PAD_OUT => PAD_OUT
        );
    end architecture rtl;
    """)
    _cell_inst = 0
    @classmethod
    def _add_instance(cls, platform, prefix, *, ir_width, ios, manufacturer, part, version):
        name = "jtag_controller_i{}".format(cls._cell_inst)
        cls._cell_inst += 1

        platform.add_file(
            "{}{}.vhdl".format(prefix, name),
            cls._controller_templ.format(
                name=name, ir_width=ir_width, ios=ios,
                manufacturer=manufacturer, part=part, version=version,
            )
        )

        return name


    def __init__(
        self, io_count, *, with_reset=False, ir_width=None,
        manufacturer_id=Const(0b10001111111, 11), part_number=Const(1, 16),
        version=Const(0, 4),
        name=None, src_loc_at=0
    ):
        assert(isinstance(io_count, int) and io_count > 0)
        assert((ir_width is None) or (isinstance(ir_width, int) and ir_width >= 2))
        assert(len(version) == 4)

        self.name = name if name is not None else get_var_name(depth=src_loc_at+2, default="TAP")
        self.bus = Interface(with_reset=with_reset, name=self.name+"_bus",
                             src_loc_at=src_loc_at+1)

        # TODO: Handle IOs with different directions
        self.core = Array(Pin(1, "io") for _ in range(io_count)) # Signals to use for core
        self.pad  = Array(Pin(1, "io") for _ in range(io_count)) # Signals going to IO pads

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
        self.__class__._add_files(platform, "jtag" + os.path.sep)

        m = Module()

        # Determine ir_width if not fixed.
        ir_max = max(self._ircodes) + 1 # One extra code needed with all ones
        ir_width = len("{:b}".format(ir_max))
        if self._ir_width is not None:
            assert self._ir_width >= ir_width, "Specified JTAG IR width not big enough for allocated shiift registers"
            ir_width = self._ir_width

        cell = self.__class__._add_instance(
            platform, "jtag" + os.path.sep, ir_width=ir_width, ios=self._io_count,
            manufacturer=self._manufacturer_id.value, part=self._part_number.value,
            version=self._version.value,
        )

        sigs = Record([
            ("capture", 1),
            ("shift", 1),
            ("update", 1),
            ("ir", ir_width),
            ("tdo_jtag", 1),
        ])

        reset = Signal()

        trst_n = Signal()
        m.d.comb += trst_n.eq(~self.bus.trst if hasattr(self.bus, "trst") else Const(1))

        core_i = Cat(pin.i for pin in self.core)
        core_o = Cat(pin.o for pin in self.core)
        core_oe = Cat(pin.oe for pin in self.core)
        pad_i = Cat(pin.i for pin in self.pad)
        pad_o = Cat(pin.o for pin in self.pad)
        pad_oe = Cat(pin.oe for pin in self.pad)

        m.submodules.tap = Instance(cell,
            i_TCK=self.bus.tck,
            i_TMS=self.bus.tms,
            i_TDI=self.bus.tdi,
            o_TDO=sigs.tdo_jtag,
            i_TRST_N=trst_n,
            o_RESET=reset,
            o_CAPTURE=sigs.capture,
            o_SHIFT=sigs.shift,
            o_UPDATE=sigs.update,
            o_IR=sigs.ir,
            o_CORE_IN=core_i,
            i_CORE_OUT=core_o,
            i_CORE_EN=core_oe,
            i_PAD_IN=pad_i,
            o_PAD_OUT=pad_o,
            o_PAD_EN=pad_oe,
        )

        # Own clock domain using TCK as clock signal
        m.domains.jtag = jtag_cd = ClockDomain(name="jtag", local=True)
        m.d.comb += [
            jtag_cd.clk.eq(self.bus.tck),
            jtag_cd.rst.eq(reset),
        ]

        self._elaborate_shiftregs(m, sigs)
        self._elaborate_wishbones(m)

        return m


    def add_shiftreg(self, ircode, length, domain="sync", name=None, src_loc_at=0):
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
            if not isinstance(_ircode, int) or _ircode <= 0:
                raise ValueError("IR code '{}' is not an int greater than 0".format(_ircode))
            if _ircode in self._ircodes:
                raise ValueError("IR code '{}' already taken".format(_ircode))

        self._ircodes.extend(ircodes)

        if name is None:
            name = self.name + "_sr{}".format(len(self._srs))
        sr = ShiftReg(sr_length=length, cmds=len(ircodes), name=name, src_loc_at=src_loc_at+1)
        self._srs.append((ircodes, domain, sr))

        return sr

    def _elaborate_shiftregs(self, m, sigs):
        # tdos is tuple of (tdo, tdo_en) for each shiftreg
        tdos = []
        for ircodes, domain, sr in self._srs:
            reg = Signal(len(sr.o), name=sr.name+"_reg")
            m.d.comb += sr.o.eq(reg)

            isir = Signal(len(ircodes), name=sr.name+"_isir")
            capture = Signal(name=sr.name+"_capture")
            shift = Signal(name=sr.name+"_shift")
            update = Signal(name=sr.name+"_update")
            m.d.comb += [
                isir.eq(Cat(sigs.ir == ircode for ircode in ircodes)),
                capture.eq((isir != 0) & sigs.capture),
                shift.eq((isir != 0) & sigs.shift),
                update.eq((isir != 0) & sigs.update),
            ]

            # update signal is on the JTAG clockdomain, sr.oe is on `domain` clockdomain
            # latch update in `domain` clockdomain and see when it has falling edge.
            # At that edge put isir in sr.oe for one `domain` clockdomain
            update_core = Signal(name=sr.name+"_update_core")
            update_core_prev = Signal(name=sr.name+"_update_core_prev")
            m.d[domain] += [
                update_core.eq(update), # This is CDC from JTAG domain to given domain
                update_core_prev.eq(update_core)
            ]
            with m.If(update_core_prev & ~update_core == 0):
                # Falling edge of update
                m.d[domain] += sr.oe.eq(isir)
            with m.Else():
                m.d[domain] += sr.oe.eq(0)

            with m.If(shift):
                m.d.jtag += reg.eq(Cat(reg[1:], self.bus.tdi))
            with m.If(capture):
                m.d.jtag += reg.eq(sr.i)

            # tdo = reg[0], tdo_en = shift
            tdos.append((reg[0], shift))

        for i, (tdo, tdo_en) in enumerate(tdos):
            if i == 0:
                with m.If(shift):
                    m.d.comb += self.bus.tdo.eq(tdo)
            else:
                with m.Elif(shift):
                    m.d.comb += self.bus.tdo.eq(tdo)

        if len(tdos) > 0:
            with m.Else():
                m.d.comb += self.bus.tdo.eq(sigs.tdo_jtag)
        else:
            # Always connect tdo_jtag to 
            m.d.comb += self.bus.tdo.eq(sigs.tdo_jtag)


    def add_wishbone(self, *, ircodes, address_width, data_width, granularity=None, domain="sync"):
        """Add a wishbone interface

        In order to allow high JTAG clock speed, data will be cached. This means that if data is
        output the value of the next address will be read automatically.

        Parameters:
        -----------
        ircodes: sequence of three integer for the JTAG IR codes;
          they represent resp. WBADDR, WBREAD and WBREADWRITE. First code
          has a shift register of length 'address_width', the two other codes
          share a shift register of length data_width.
        address_width: width of the address
        data_width: width of the data

        Returns:
        wb: nmigen_soc.wishbone.bus.Interface
            The Wishbone interface, is pipelined and has stall field.
        """
        if len(ircodes) != 3:
            raise ValueError("3 IR Codes have to be provided")

        sr_addr = self.add_shiftreg(ircodes[0], address_width, domain=domain)
        sr_data = self.add_shiftreg(ircodes[1:], data_width, domain=domain)

        wb = WishboneInterface(data_width=data_width, addr_width=address_width,
                               granularity=granularity, features={"stall", "lock", "err", "rty"})

        self._wbs.append((sr_addr, sr_data, wb, domain))

        return wb

    def _elaborate_wishbones(self, m):
        for sr_addr, sr_data, wb, domain in self._wbs:
            if hasattr(wb, "sel"):
                # Always selected
                m.d.comb += [s.eq(1) for s in wb.sel]

            with m.FSM(domain=domain) as fsm:
                with m.State("IDLE"):
                    with m.If(sr_addr.oe): # WBADDR code
                        m.d[domain] += wb.adr.eq(sr_addr.o)
                        m.next = "READ"
                    with m.Elif(sr_data.oe[0]): # WBREAD code
                        # If data is
                        m.d[domain] += wb.adr.eq(wb.adr + 1)
                        m.next = "READ"
                    with m.Elif(sr_data.oe[1]): # WBWRITE code
                        m.d[domain] += wb.dat_w.eq(sr_data.o)
                        m.next = "WRITEREAD"
                with m.State("READ"):
                    with m.If(~wb.stall):
                        m.next = "READACK"
                with m.State("READACK"):
                    with m.If(wb.ack):
                        # Store read data in sr_data.i and keep it there til next read
                        m.d[domain] += sr_data.i.eq(wb.dat_r)
                        m.next = "IDLE"
                with m.State("WRITEREAD"):
                    with m.If(~wb.stall):
                        m.next = "WRITEREADACK"
                with m.State("WRITEREADACK"):
                    with m.If(wb.ack):
                        m.d[domain] += wb.adr.eq(wb.adr + 1)
                        m.next = "READ"

                m.d.comb += [
                    wb.cyc.eq(~fsm.ongoing("IDLE")),
                    wb.stb.eq(fsm.ongoing("READ") | fsm.ongoing("WRITEREAD")),
                    wb.we.eq(fsm.ongoing("WRITEREAD")),
                ]
