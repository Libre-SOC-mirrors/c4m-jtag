#!/usr/bin/env python3
import os, textwrap
from enum import Enum, auto

from nmigen import (Elaboratable, Signal, Module, ClockDomain, Cat, Record,
                    Const, Mux)
from nmigen.hdl.rec import Direction, Layout
from nmigen.tracer import get_var_name

from nmigen_soc.wishbone import Interface as WishboneInterface

from .bus import Interface, DMIInterface

__all__ = [
    "TAP", "ShiftReg", "IOType", "IOConn",
]


class _FSM(Elaboratable):
    """TAP subblock for the FSM"""
    def __init__(self, *, bus):
        self.isir = Signal()
        self.isdr = Signal()
        self.capture = Signal()
        self.shift = Signal()
        self.update = Signal()

        # JTAG uses both edges of the incoming clock (TCK). set them up here
        self.posjtag = ClockDomain("posjtag", local=True)
        self.negjtag = ClockDomain("negjtag", local=True, clk_edge="neg")

        self._bus = bus

    def elaborate(self, platform):
        m = Module()

        rst = Signal()
        m.d.comb += [
            self.posjtag.clk.eq(self._bus.tck),
            self.posjtag.rst.eq(rst),
            self.negjtag.clk.eq(self._bus.tck),
            self.negjtag.rst.eq(rst),
        ]

        # Make local clock domain optionally using trst of JTAG bus as reset
        if hasattr(self._bus, "trst"):
            m.domains.local = local = ClockDomain(local=True)
            m.d.comb += local.rst.eq(self._bus.trst)
        else:
            m.domains.local = local = ClockDomain(local=True, reset_less=True)
        m.d.comb += local.clk.eq(self._bus.tck)

        with m.FSM(domain="local") as fsm:
            with m.State("TestLogicReset"):
                # Be sure to reset isir, isdr
                m.d.local += [
                    self.isir.eq(0),
                    self.isdr.eq(0),
                ]
                with m.If(self._bus.tms == 0):
                    m.next = "RunTestIdle"
            with m.State("RunTestIdle"):
                # Be sure to reset isir, isdr
                m.d.local += [
                    self.isir.eq(0),
                    self.isdr.eq(0),
                ]
                with m.If(self._bus.tms == 1):
                    m.next = "SelectDRScan"
            with m.State("SelectDRScan"):
                with m.If(self._bus.tms == 0):
                    m.d.local += self.isdr.eq(1)
                    m.next = "CaptureState"
                with m.Else():
                    m.next = "SelectIRScan"
            with m.State("SelectIRScan"):
                with m.If(self._bus.tms == 0):
                    m.d.local += self.isir.eq(1)
                    m.next = "CaptureState"
                with m.Else():
                    m.next = "TestLogicReset"
            with m.State("CaptureState"):
                with m.If(self._bus.tms == 0):
                    m.next = "ShiftState"
                with m.Else():
                    m.next = "Exit1"
            with m.State("ShiftState"):
                with m.If(self._bus.tms == 1):
                    m.next = "Exit1"
            with m.State("Exit1"):
                with m.If(self._bus.tms == 0):
                    m.next = "Pause"
                with m.Else():
                    m.next = "UpdateState"
            with m.State("Pause"):
                with m.If(self._bus.tms == 1):
                    m.next = "Exit2"
            with m.State("Exit2"):
                with m.If(self._bus.tms == 0):
                    m.next = "ShiftState"
                with m.Else():
                    m.next = "UpdateState"
            with m.State("UpdateState"):
                m.d.local += [
                    self.isir.eq(0),
                    self.isdr.eq(0),
                ]
                with m.If(self._bus.tms == 0):
                    m.next = "RunTestIdle"
                with m.Else():
                    m.next = "SelectDRScan"

            m.d.comb += [
                rst.eq(fsm.ongoing("TestLogicReset")),
                self.capture.eq(fsm.ongoing("CaptureState")),
                self.shift.eq(fsm.ongoing("ShiftState")),
                self.update.eq(fsm.ongoing("UpdateState")),
            ]

        return m


class _IRBlock(Elaboratable):
    """TAP subblock for handling the IR shift register"""
    def __init__(self, *, ir_width, cmd_idcode,
                 tdi, capture, shift, update,
                 name):
        self.name = name
        self.ir = Signal(ir_width, reset=cmd_idcode)
        self.tdo = Signal()

        self._tdi = tdi
        self._capture = capture
        self._shift = shift
        self._update = update

    def elaborate(self, platform):
        m = Module()

        shift_ir = Signal(len(self.ir), reset_less=True)

        m.d.comb += self.tdo.eq(self.ir[0])
        with m.If(self._capture):
            m.d.posjtag += shift_ir.eq(self.ir)
        with m.Elif(self._shift):
            m.d.posjtag += shift_ir.eq(Cat(shift_ir[1:], self._tdi))
        with m.Elif(self._update):
            # For ir we only update it on the rising edge of clock
            # to avoid that we already have the new ir value when still in
            # Update state
            m.d.posjtag += self.ir.eq(shift_ir)

        return m


class IOType(Enum):
    In = auto()
    Out = auto()
    TriOut = auto()
    InTriOut = auto()


class IOConn(Record):
    lengths = {
        IOType.In: 1,
        IOType.Out: 1,
        IOType.TriOut: 2,
        IOType.InTriOut: 3,
    }

    """TAP subblock representing the interface for an JTAG IO cell.
    It contains signal to connect to the core and to the pad

    This object is normally only allocated and returned from ``TAP.add_io``
    It is a Record subclass.

    Attributes
    ----------
    core: subrecord with signals for the core
        i: Signal(1), present only for IOType.In and IOType.InTriOut.
            Signal input to core with pad input value.
        o: Signal(1), present only for IOType.Out, IOType.TriOut and
            IOType.InTriOut.
            Signal output from core with the pad output value.
        oe: Signal(1), present only for IOType.TriOut and IOType.InTriOut.
            Signal output from core with the pad output enable value.
    pad: subrecord with for the pad
        i: Signal(1), present only for IOType.In and IOType.InTriOut
            Output from pad with pad input value for core.
        o: Signal(1), present only for IOType.Out, IOType.TriOut and
            IOType.InTriOut.
            Input to pad with pad output value.
        oe: Signal(1), present only for IOType.TriOut and IOType.InTriOut.
            Input to pad with pad output enable value.
    """
    @staticmethod
    def layout(iotype):
        sigs = []
        if iotype in (IOType.In, IOType.InTriOut):
            sigs.append(("i", 1))
        if iotype in (IOType.Out, IOType.TriOut, IOType.InTriOut):
            sigs.append(("o", 1))
        if iotype in (IOType.TriOut, IOType.InTriOut):
            sigs.append(("oe", 1))

        return Layout((("core", sigs), ("pad", sigs)))

    def __init__(self, *, iotype, name=None, src_loc_at=0):
        super().__init__(self.__class__.layout(iotype), name=name,
                         src_loc_at=src_loc_at+1)

        self._iotype = iotype


class _IDBypassBlock(Elaboratable):
    """TAP subblock for the ID shift register"""
    def __init__(self, *, manufacturer_id, part_number, version,
                 tdi, capture, shift, update, bypass,
                 name):
        self.name = name
        if (not isinstance(manufacturer_id, Const) and
            len(manufacturer_id) != 11):
            raise ValueError("manufacturer_id has to be Const of length 11")
        if not isinstance(part_number, Const) and len(manufacturer_id) != 16:
            raise ValueError("part_number has to be Const of length 16")
        if not isinstance(version, Const) and len(version) != 4:
            raise ValueError("version has to be Const of length 4")
        self._id = Cat(Const(1,1), manufacturer_id, part_number, version)

        self.tdo = Signal(name=name+"_tdo")

        self._tdi = tdi
        self._capture = capture
        self._shift = shift
        self._update = update
        self._bypass = bypass

    def elaborate(self, platform):
        m = Module()

        sr = Signal(32, reset_less=True, name=self.name+"_sr")

        # Local signals for the module
        _tdi = Signal()
        _capture = Signal()
        _shift = Signal()
        _update = Signal()
        _bypass = Signal()

        m.d.comb += [
            _tdi.eq(self._tdi),
            _capture.eq(self._capture),
            _shift.eq(self._shift),
            _update.eq(self._update),
            _bypass.eq(self._bypass),
            self.tdo.eq(sr[0]),
        ]

        with m.If(_capture):
            m.d.posjtag += sr.eq(self._id)
        with m.Elif(_shift):
            with m.If(_bypass):
                m.d.posjtag += sr[0].eq(_tdi)
            with m.Else():
                m.d.posjtag += sr.eq(Cat(sr[1:], _tdi))

        return m


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
        Indicates that output is stable and can be sampled downstream because
        JTAG TAP is in the Update state. The bit indicates the corresponding
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
    def __init__(self, *, with_reset=False, ir_width=None,
                 manufacturer_id=Const(0b10001111111, 11),
                 part_number=Const(1, 16),
                 version=Const(0, 4),
                 name=None, src_loc_at=0):
        assert((ir_width is None) or (isinstance(ir_width, int) and
               ir_width >= 2))
        assert(len(version) == 4)

        if name is None:
            name = get_var_name(depth=src_loc_at+2, default="TAP")
        self.name = name
        self.bus = Interface(with_reset=with_reset, name=self.name+"_bus",
                             src_loc_at=src_loc_at+1)

        ##

        self._ir_width = ir_width
        self._manufacturer_id = manufacturer_id
        self._part_number = part_number
        self._version = version

        self._ircodes = [0, 1, 2] # Already taken codes, all ones added at end

        self._ios = []
        self._srs = []
        self._wbs = []
        self._dmis = []

    def elaborate(self, platform):
        m = Module()

        # Determine ir_width if not fixed.
        ir_max = max(self._ircodes) + 1 # One extra code needed with all ones
        ir_width = len("{:b}".format(ir_max))
        if self._ir_width is not None:
            assert self._ir_width >= ir_width, "Specified JTAG IR width " \
                   "not big enough for allocated shiift registers"
            ir_width = self._ir_width

        # TODO: Make commands numbers configurable
        cmd_extest = 0
        cmd_intest = 0
        cmd_idcode = 1
        cmd_sample = 2
        cmd_preload = 2
        cmd_bypass = 2**ir_width - 1 # All ones

        m.submodules._fsm = fsm = _FSM(bus=self.bus)
        m.domains.posjtag = fsm.posjtag
        m.domains.negjtag = fsm.negjtag

        # IR block
        select_ir = fsm.isir
        m.submodules._irblock = irblock = _IRBlock(
            ir_width=ir_width, cmd_idcode=cmd_idcode, tdi=self.bus.tdi,
            capture=(fsm.isir & fsm.capture),
            shift=(fsm.isir & fsm.shift),
            update=(fsm.isir & fsm.update),
            name=self.name+"_ir",
        )
        ir = irblock.ir

        # ID block
        select_id = Signal()
        id_bypass = Signal()
        m.d.comb += select_id.eq(fsm.isdr &
                                 ((ir == cmd_idcode) | (ir == cmd_bypass)))
        m.d.comb += id_bypass.eq(ir == cmd_bypass)
        m.submodules._idblock = idblock = _IDBypassBlock(
            manufacturer_id=self._manufacturer_id,
            part_number=self._part_number,
            version=self._version, tdi=self.bus.tdi,
            capture=(select_id & fsm.capture),
            shift=(select_id & fsm.shift),
            update=(select_id & fsm.update),
            bypass=id_bypass,
            name=self.name+"_id",
        )

        # IO (Boundary scan) block
        io_capture = Signal()
        io_shift = Signal()
        io_update = Signal()
        io_bd2io = Signal()
        io_bd2core = Signal()
        sample = (ir == cmd_extest) | (ir == cmd_sample)
        preload = (ir == cmd_preload)
        select_io = fsm.isdr & (sample | preload)
        m.d.comb += [
            io_capture.eq(sample & fsm.capture), # Don't capture if not sample
                                                 # (like for PRELOAD)
            io_shift.eq(select_io & fsm.shift),
            io_update.eq(select_io & fsm.update),
            io_bd2io.eq(ir == cmd_extest),
            io_bd2core.eq(ir == cmd_intest),
        ]
        io_tdo = self._elaborate_ios(
            m=m,
            capture=io_capture, shift=io_shift, update=io_update,
            bd2io=io_bd2io, bd2core=io_bd2core,
        )

        # chain tdo: select as appropriate, to go into into shiftregs
        tdo = Signal(name=self.name+"_tdo")
        with m.If(select_ir):
            m.d.comb += tdo.eq(irblock.tdo)
        with m.Elif(select_id):
            m.d.comb += tdo.eq(idblock.tdo)
        with m.Elif(select_io):
            m.d.comb += tdo.eq(io_tdo)

        # shiftregs block
        self._elaborate_shiftregs(
            m, capture=fsm.capture, shift=fsm.shift, update=fsm.update,
            ir=irblock.ir, tdo_jtag=tdo
        )

        # wishbone
        self._elaborate_wishbones(m)

        # DMI (Debug Memory Interface)
        self._elaborate_dmis(m)

        return m

    def add_dmi(self, *, ircodes, address_width=8, data_width=64,
                     domain="sync", name=None):
        """Add a DMI interface

        * writing to DMIADDR will automatically trigger a DMI READ.
          the DMI address does not alter (so writes can be done at that addr)
        * reading from DMIREAD triggers a DMI READ at the current DMI addr
          the address is automatically incremented by 1 after.
        * writing to DMIWRITE triggers a DMI WRITE at the current DMI addr
          the address is automatically incremented by 1 after.

        Parameters:
        -----------
        ircodes: sequence of three integer for the JTAG IR codes;
                 they represent resp. DMIADDR, DMIREAD and DMIWRITE.
                 First code has a shift register of length 'address_width',
                 the two other codes share a shift register of length
                data_width.

        address_width: width of the address
        data_width: width of the data

        Returns:
        dmi: soc.debug.dmi.DMIInterface
            The DMI interface
        """
        if len(ircodes) != 3:
            raise ValueError("3 IR Codes have to be provided")

        if name is None:
            name = "dmi" + str(len(self._dmis))

        # add 2 shift registers: one for addr, one for data.
        sr_addr = self.add_shiftreg(ircode=ircodes[0], length=address_width,
                                     domain=domain, name=name+"_addrsr")
        sr_data = self.add_shiftreg(ircode=ircodes[1:], length=data_width,
                                    domain=domain, name=name+"_datasr")

        dmi = DMIInterface(name=name)
        self._dmis.append((sr_addr, sr_data, dmi, domain))

        return dmi

    def _elaborate_dmis(self, m):
        for sr_addr, sr_data, dmi, domain in self._dmis:
            cd = m.d[domain]
            m.d.comb += sr_addr.i.eq(dmi.addr_i)

            with m.FSM(domain=domain) as ds:

                # detect mode based on whether jtag addr or data read/written
                with m.State("IDLE"):
                    with m.If(sr_addr.oe): # DMIADDR code
                        cd += dmi.addr_i.eq(sr_addr.o)
                        m.next = "READ"
                    with m.Elif(sr_data.oe[0]): # DMIREAD code
                        # If data is
                        cd += dmi.addr_i.eq(dmi.addr_i + 1)
                        m.next = "READ"
                    with m.Elif(sr_data.oe[1]): # DMIWRITE code
                        cd += dmi.din.eq(sr_data.o)
                        m.next = "WRRD"

                # req_i raises for 1 clock
                with m.State("READ"):
                    m.next = "READACK"

                # wait for read ack
                with m.State("READACK"):
                    with m.If(dmi.ack_o):
                        # Store read data in sr_data.i hold till next read
                        cd += sr_data.i.eq(dmi.dout)
                        m.next = "IDLE"

                # req_i raises for 1 clock
                with m.State("WRRD"):
                    m.next = "WRRDACK"

                # wait for write ack
                with m.State("WRRDACK"):
                    with m.If(dmi.ack_o):
                        cd += dmi.addr_i.eq(dmi.addr_i + 1)
                        m.next = "READ" # for readwrite

                # set DMI req and write-enable based on ongoing FSM states
                m.d.comb += [
                    dmi.req_i.eq(ds.ongoing("READ") | ds.ongoing("WRRD")),
                    dmi.we_i.eq(ds.ongoing("WRRD")),
                ]

    def add_io(self, *, iotype, name=None, src_loc_at=0):
        """Add a io cell to the boundary scan chain

        Parameters:
        - iotype: :class:`IOType` enum.

        Returns:
        - :class:`IOConn`
        """
        if name is None:
            name = "ioconn" + str(len(self._ios))

        ioconn = IOConn(iotype=iotype, name=name, src_loc_at=src_loc_at+1)
        self._ios.append(ioconn)
        return ioconn

    def _elaborate_ios(self, *, m, capture, shift, update, bd2io, bd2core):
        length = sum(IOConn.lengths[conn._iotype] for conn in self._ios)
        if length == 0:
            return self.bus.tdi

        io_sr = Signal(length)
        io_bd = Signal(length)

        # Boundary scan "capture" mode.  makes I/O status available via SR
        with m.If(capture):
            iol = []
            idx = 0
            for conn in self._ios:
                # in appropriate sequence: In/TriOut has pad.i,
                # Out.InTriOut has everything, Out and TriOut have core.o
                if conn._iotype in [IOType.In, IOType.InTriOut]:
                    iol.append(conn.pad.i)
                if conn._iotype in [IOType.Out, IOType.InTriOut]:
                    iol.append(conn.core.o)
                if conn._iotype in [IOType.TriOut, IOType.InTriOut]:
                    iol.append(conn.core.oe)
                # length double-check
                idx += IOConn.lengths[conn._iotype] # fails if wrong type
            assert idx == length, "Internal error"
            m.d.posjtag += io_sr.eq(Cat(*iol)) # assigns all io_sr in one hit

        # "Shift" mode (sends out captured data on tdo, sets incoming from tdi)
        with m.Elif(shift):
            m.d.posjtag += io_sr.eq(Cat(self.bus.tdi, io_sr[:-1]))

        # "Update" mode
        with m.Elif(update):
            m.d.negjtag += io_bd.eq(io_sr)

        # sets up IO (pad<->core) or in testing mode depending on requested
        # mode, via Muxes controlled by bd2core and bd2io
        idx = 0
        for conn in self._ios:
            if conn._iotype == IOType.In:
                m.d.comb += conn.core.i.eq(Mux(bd2core, io_bd[idx], conn.pad.i))
                idx += 1
            elif conn._iotype == IOType.Out:
                m.d.comb += conn.pad.o.eq(Mux(bd2io, io_bd[idx], conn.core.o))
                idx += 1
            elif conn._iotype == IOType.TriOut:
                m.d.comb += [
                    conn.pad.o.eq(Mux(bd2io, io_bd[idx], conn.core.o)),
                    conn.pad.oe.eq(Mux(bd2io, io_bd[idx+1], conn.core.oe)),
                ]
                idx += 2
            elif conn._iotype == IOType.InTriOut:
                m.d.comb += [
                    conn.core.i.eq(Mux(bd2core, io_bd[idx], conn.pad.i)),
                    conn.pad.o.eq(Mux(bd2io, io_bd[idx+1], conn.core.o)),
                    conn.pad.oe.eq(Mux(bd2io, io_bd[idx+2], conn.core.oe)),
                ]
                idx += 3
            else:
                raise("Internal error")
        assert idx == length, "Internal error"

        return io_sr[-1]

    def add_shiftreg(self, *, ircode, length, domain="sync", name=None,
                     src_loc_at=0):
        """Add a shift register to the JTAG interface

        Parameters:
        - ircode: code(s) for the IR; int or sequence of ints. In the latter
          case this shiftreg is shared between different IR codes.
        - length: the length of the shift register
        - domain: the domain on which the signal will be used"""

        try:
            ir_it = iter(ircode)
            ircodes = ircode
        except TypeError:
            ir_it = ircodes = (ircode,)
        for _ircode in ir_it:
            if not isinstance(_ircode, int) or _ircode <= 0:
                raise ValueError("IR code '{}' is not an int "
                                 "greater than 0".format(_ircode))
            if _ircode in self._ircodes:
                raise ValueError("IR code '{}' already taken".format(_ircode))

        self._ircodes.extend(ircodes)

        if name is None:
            name = "sr{}".format(len(self._srs))
        sr = ShiftReg(sr_length=length, cmds=len(ircodes), name=name,
                      src_loc_at=src_loc_at+1)
        self._srs.append((ircodes, domain, sr))

        return sr

    def _elaborate_shiftregs(self, m, capture, shift, update, ir, tdo_jtag):
        # tdos is tuple of (tdo, tdo_en) for each shiftreg
        tdos = []
        for ircodes, domain, sr in self._srs:
            reg = Signal(len(sr.o), name=sr.name+"_reg")
            m.d.comb += sr.o.eq(reg)

            isir = Signal(len(ircodes), name=sr.name+"_isir")
            sr_capture = Signal(name=sr.name+"_capture")
            sr_shift = Signal(name=sr.name+"_shift")
            sr_update = Signal(name=sr.name+"_update")
            m.d.comb += [
                isir.eq(Cat(ir == ircode for ircode in ircodes)),
                sr_capture.eq((isir != 0) & capture),
                sr_shift.eq((isir != 0) & shift),
                sr_update.eq((isir != 0) & update),
            ]

            # update signal is on the JTAG clockdomain, sr.oe is on `domain`
            # clockdomain latch update in `domain` clockdomain and see when
            # it has falling edge.
            # At that edge put isir in sr.oe for one `domain` clockdomain
            # Using this custom sync <> JTAG domain synchronization avoids
            # the use of more generic but also higher latency CDC solutions
            # like FFSynchronizer.
            update_core = Signal(name=sr.name+"_update_core")
            update_core_prev = Signal(name=sr.name+"_update_core_prev")
            m.d[domain] += [
                update_core.eq(sr_update), # This is CDC from JTAG domain
                                           # to given domain
                update_core_prev.eq(update_core)
            ]
            with m.If(update_core_prev & ~update_core):
                # Falling edge of update
                m.d[domain] += sr.oe.eq(isir)
            with m.Else():
                m.d[domain] += sr.oe.eq(0)

            with m.If(sr_shift):
                m.d.posjtag += reg.eq(Cat(reg[1:], self.bus.tdi))
            with m.If(sr_capture):
                m.d.posjtag += reg.eq(sr.i)

            # tdo = reg[0], tdo_en = shift
            tdos.append((reg[0], sr_shift))


        # Assign the right tdo to the bus tdo
        for i, (tdo, tdo_en) in enumerate(tdos):
            if i == 0:
                with m.If(tdo_en):
                    m.d.comb += self.bus.tdo.eq(tdo)
            else:
                with m.Elif(tdo_en):
                    m.d.comb += self.bus.tdo.eq(tdo)

        if len(tdos) > 0:
            with m.Else():
                m.d.comb += self.bus.tdo.eq(tdo_jtag)
        else:
            # Always connect tdo_jtag to
            m.d.comb += self.bus.tdo.eq(tdo_jtag)


    def add_wishbone(self, *, ircodes, address_width, data_width,
                     granularity=None, domain="sync", features=None,
                     name=None, src_loc_at=0):
        """Add a wishbone interface

        In order to allow high JTAG clock speed, data will be cached.
        This means that if data is output the value of the next address
        will be read automatically.

        Parameters:
        -----------
        ircodes: sequence of three integer for the JTAG IR codes;
          they represent resp. WBADDR, WBREAD and WBREADWRITE. First code
          has a shift register of length 'address_width', the two other codes
          share a shift register of length data_width.
        address_width: width of the address
        data_width: width of the data
        features: features required.  defaults to stall, lock, err, rty

        Returns:
        wb: nmigen_soc.wishbone.bus.Interface
            The Wishbone interface, is pipelined and has stall field.
        """
        if len(ircodes) != 3:
            raise ValueError("3 IR Codes have to be provided")

        if features is None:
            features={"stall", "lock", "err", "rty"}
        if name is None:
            name = "wb" + str(len(self._wbs))
        sr_addr = self.add_shiftreg(
            ircode=ircodes[0], length=address_width, domain=domain,
            name=name+"_addrsr"
        )
        sr_data = self.add_shiftreg(
            ircode=ircodes[1:], length=data_width, domain=domain,
            name=name+"_datasr"
        )

        wb = WishboneInterface(data_width=data_width, addr_width=address_width,
                               granularity=granularity, features=features,
                               name=name, src_loc_at=src_loc_at+1)

        self._wbs.append((sr_addr, sr_data, wb, domain))

        return wb

    def _elaborate_wishbones(self, m):
        for sr_addr, sr_data, wb, domain in self._wbs:
            m.d.comb += sr_addr.i.eq(wb.adr)

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
                    if not hasattr(wb, "stall"):
                        m.next = "READACK"
                    else:
                        with m.If(~wb.stall):
                            m.next = "READACK"
                with m.State("READACK"):
                    with m.If(wb.ack):
                        # Store read data in sr_data.i
                        # and keep it there til next read.
                        # This is enough to synchronize between sync and JTAG
                        # clock domain and no higher latency solutions like
                        # FFSynchronizer is needed.
                        m.d[domain] += sr_data.i.eq(wb.dat_r)
                        m.next = "IDLE"
                with m.State("WRITEREAD"):
                    if not hasattr(wb, "stall"):
                        m.next = "WRITEREADACK"
                    else:
                        with m.If(~wb.stall):
                            m.next = "WRITEREADACK"
                with m.State("WRITEREADACK"):
                    with m.If(wb.ack):
                        m.d[domain] += wb.adr.eq(wb.adr + 1)
                        m.next = "READ"

                if hasattr(wb, "stall"):
                    m.d.comb += wb.stb.eq(fsm.ongoing("READ") |
                                          fsm.ongoing("WRITEREAD"))
                else:
                    # non-stall is single-cycle (litex), must assert stb
                    # until ack is sent
                    m.d.comb += wb.stb.eq(fsm.ongoing("READ") |
                                          fsm.ongoing("WRITEREAD") |
                                          fsm.ongoing("READACK") |
                                          fsm.ongoing("WRITEREADACK"))
                m.d.comb += [
                    wb.cyc.eq(~fsm.ongoing("IDLE")),
                    wb.we.eq(fsm.ongoing("WRITEREAD")),
                ]
