import cocotb
from cocotb.utils import get_sim_steps
from cocotb.binary import BinaryValue
from cocotb.triggers import Timer, RisingEdge, ReadOnly
from cocotb.clock import Clock

from c4m.cocotb.jtag.c4m_jtag import JTAG_Master

from cocotbext.wishbone import WishboneBus


class WishboneMemory(object):
    def __init__(self, bus):
        self.bus = bus
        self._mem = {}
        self._adr_width = len(self.bus.adr)
        self._dat_width = len(self.bus.datrd)
        self._dat_x = BinaryValue(self._dat_width * "X")

    @cocotb.coroutine
    def start(self):
        while True:
            yield self.bus.clock_event
            if self.bus.cyc.value and self.bus.stb.value:
                adr = self.bus.adr.value.integer
                # Immediately ack a cycle
                self.bus.ack <= 1
                if self.bus.we.value:
                    # Write
                    self._mem[adr] = self.bus.datwr.value
                    self.bus.datrd <= self._dat_x
                else:
                    # Read
                    if adr in self._mem:
                        self.bus.datrd <= self._mem[adr]
                    else:
                        self.bus.datrd <= self._dat_x
            else:
                self.bus.ack <= 0
                self.bus.datrd <= self._dat_x

    def __repr__(self):
        return "WishboneMemory: {!r}".format(self._mem)

@cocotb.test()
def test01_idcode(dut):
    """
    Test the IDCODE command
    """

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(
        dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo,
        clk_period=clk_period, ir_width=3,
    )

    dut._log.info("Trying to get IDCODE...")

    yield master.idcode()
    result1 = master.result
    dut._log.info("IDCODE1: {}".format(result1))

    yield master.idcode()
    result2 = master.result
    dut._log.info("IDCODE2: {}".format(result2))

    assert(result1 == result2)
    

@cocotb.test()
def test02_bypass(dut):
    """
    Test of BYPASS mode
    """

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(
        dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo,
        clk_period=clk_period, ir_width=3,
    )

    dut._log.info("Loading BYPASS command")
    yield master.load_ir(master.BYPASS)

    data_in = BinaryValue()
    data_in.binstr = "01001101"
    dut._log.info("  Sending data: {}".format(data_in.binstr))
    yield master.shift_data(data_in)

    dut._log.info("  bypass out: {}".format(master.result.binstr))
    assert(master.result.binstr[:-1] == data_in.binstr[1:])


@cocotb.test()
def test03_sample(dut):
    """
    Test of SAMPLEPRELOAD and EXTEST
    """
    data_in = BinaryValue()

    dut.rst = 1
    yield Timer(100, "ns")
    dut.rst = 0

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(
        dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo,
        clk_period=clk_period, ir_width=3,
    )


    dut._log.info("Load SAMPLEPRELOAD command")
    yield master.load_ir(master.SAMPLEPRELOAD)

    data_in.binstr = "0100110"
    dut._log.info("  preloading data {}".format(data_in.binstr))

    # Set the ios pins
    dut.ioconn0__pad__i = 1
    dut.ioconn1__core__o = 0
    dut.ioconn2__core__o = 1
    dut.ioconn2__core__oe = 1
    dut.ioconn3__pad__i = 0
    dut.ioconn3__core__o = 0
    dut.ioconn3__core__oe = 1
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "1011001")

    assert dut.ioconn0__core__i == 1
    assert dut.ioconn1__pad__o == 0
    assert dut.ioconn2__pad__o == 1
    assert dut.ioconn2__pad__oe == 1
    assert dut.ioconn3__core__i == 0
    assert dut.ioconn3__pad__o == 0
    assert dut.ioconn3__pad__oe == 1

    dut._log.info("Load EXTEST command")
    yield master.load_ir(master.EXTEST)

    assert dut.ioconn0__core__i == 0
    assert dut.ioconn1__pad__o == 1
    assert dut.ioconn2__pad__o == 0
    assert dut.ioconn2__pad__oe == 0
    assert dut.ioconn3__core__i == 1
    assert dut.ioconn3__pad__o == 1
    assert dut.ioconn3__pad__oe == 0

    data_in.binstr = "1011001"
    dut._log.info("  input data {}".format(data_in.binstr))
    
    # Set the ios pins
    dut.ioconn0__pad__i = 0
    dut.ioconn1__core__o = 1
    dut.ioconn2__core__o = 0
    dut.ioconn2__core__oe = 0
    dut.ioconn3__pad__i = 1
    dut.ioconn3__core__o = 1
    dut.ioconn3__core__oe = 0
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "0100110")

    assert dut.ioconn0__core__i == 1
    assert dut.ioconn1__pad__o == 0
    assert dut.ioconn2__pad__o == 1
    assert dut.ioconn2__pad__oe == 1
    assert dut.ioconn3__core__i == 0
    assert dut.ioconn3__pad__o == 0
    assert dut.ioconn3__pad__oe == 1

    yield master.reset()

    assert dut.ioconn0__core__i == 0
    assert dut.ioconn1__pad__o == 1
    assert dut.ioconn2__pad__o == 0
    assert dut.ioconn2__pad__oe == 0
    assert dut.ioconn3__core__i == 1
    assert dut.ioconn3__pad__o == 1
    assert dut.ioconn3__pad__oe == 0


@cocotb.test()
def test04_shiftreg(dut):
    """
    Test of custom shiftreg
    """
    data_in = BinaryValue()
    cmd_SR = BinaryValue("011")

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(
        dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo,
        clk_period=clk_period, ir_width=3,
    ) 


    dut._log.info("Load custom shiftreg command")
    yield master.load_ir(cmd_SR)

    data_in.binstr = "010"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))

    data_in.binstr = "101"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "010"

@cocotb.test()
def test05_wishbone(dut):
    """
    Test of an added Wishbone interface
    """
    data_in = BinaryValue()
    cmd_MEMADDRESS = BinaryValue("100")
    cmd_MEMREAD = BinaryValue("101")
    cmd_MEMREADWRITE = BinaryValue("110")

    # Run JTAG @ 1MHz
    jtagclk_period = get_sim_steps(1, "us")
    master = JTAG_Master(
        dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo,
        clk_period=jtagclk_period, ir_width=3,
    ) 
    # Run main chip @ 10MHz; need to be clocked for Wishbone interface to function
    cocotb.fork(Clock(dut.clk, 100, "ns").start())

    # Add Wishbone memory on the bus
    bus = WishboneBus(
        entity=dut.tap, name="wb0", bus_separator="__", clock=dut.clk, reset=dut.rst,
        signals={"datwr": "dat_w", "datrd": "dat_r"},
    )
    wbmem = WishboneMemory(bus)
    cocotb.fork(wbmem.start())

    # Load the memory address
    yield master.load_ir(cmd_MEMADDRESS)
    dut._log.info("Loading address")

    data_in.binstr = "1100000000000000"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))

    # Do write
    yield master.load_ir(cmd_MEMREADWRITE)
    dut._log.info("Writing memory")

    data_in.binstr = "01010101"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))

    data_in.binstr = "10101010"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))

    # Load the memory address
    yield master.load_ir(cmd_MEMADDRESS)
    dut._log.info("Loading address")

    data_in.binstr = "1100000000000000"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "1100000000000010"

    # Do read and write
    yield master.load_ir(cmd_MEMREADWRITE)
    dut._log.info("Reading and writing memory")

    data_in.binstr = "10101010"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "01010101"

    data_in.binstr = "01010101"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "10101010"

    # Load the memory address
    yield master.load_ir(cmd_MEMADDRESS)
    dut._log.info("Loading address")

    data_in.binstr = "1100000000000000"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "1100000000000010"

    # Do read
    yield master.load_ir(cmd_MEMREAD)
    dut._log.info("Reading memory")
    data_in.binstr = "00000000"

    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "10101010"

    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "01010101"

    # Load the memory address
    yield master.load_ir(cmd_MEMADDRESS) # MEMADDR
    dut._log.info("Loading address")

    data_in.binstr = "1100000000000000"
    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "1100000000000010"

    # Do read
    yield master.load_ir(cmd_MEMREAD) # MEMREAD
    dut._log.info("Reading memory")
    data_in.binstr = "00000000"

    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "10101010"

    dut._log.info("  input: {}".format(data_in.binstr))
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert master.result.binstr == "01010101"

    dut._log.info("{!r}".format(wbmem))
