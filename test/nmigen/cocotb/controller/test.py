import cocotb
from cocotb.utils import get_sim_steps
from cocotb.binary import BinaryValue

from c4m.cocotb.jtag.c4m_jtag import JTAG_Master


@cocotb.test()
def test01_idcode(dut):
    """
    Test the IDCODE command
    """

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo, clk_period=clk_period)

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
    master = JTAG_Master(dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo, clk_period=clk_period)

    dut._log.info("Loading BYPASS command")
    yield master.load_ir(master.BYPASS)

    dut._log.info("Sending data")

    data_in = BinaryValue()
    data_in.binstr = "01001101"
    yield master.shift_data(data_in)

    dut._log.info("bypass out: {}".format(master.result.binstr))
    assert(master.result.binstr[:-1] == data_in.binstr[1:])


@cocotb.test()
def test03_sample(dut):
    """
    Test of SAMPLEPRELOAD and EXTEST
    """
    data_in = BinaryValue()

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master = JTAG_Master(dut.tap_bus__tck, dut.tap_bus__tms, dut.tap_bus__tdi, dut.tap_bus__tdo, clk_period=clk_period)


    dut._log.info("Load SAMPLEPRELOAD command")
    yield master.load_ir(master.SAMPLEPRELOAD)

    data_in.binstr = "0100110"
    dut._log.info("  preloading data {}".format(data_in.binstr))

    # Set the ios pins
    dut.tap_ioconn0__pad__i = 1
    dut.tap_ioconn1__core__o = 0
    dut.tap_ioconn2__core__o = 1
    dut.tap_ioconn2__core__oe = 1
    dut.tap_ioconn3__pad__i = 0
    dut.tap_ioconn3__core__o = 0
    dut.tap_ioconn3__core__oe = 1
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "1011001")

    assert dut.tap_ioconn0__core__i == 1
    assert dut.tap_ioconn1__pad__o == 0
    assert dut.tap_ioconn2__pad__o == 1
    assert dut.tap_ioconn2__pad__oe == 1
    assert dut.tap_ioconn3__core__i == 0
    assert dut.tap_ioconn3__pad__o == 0
    assert dut.tap_ioconn3__pad__oe == 1

    dut._log.info("Load EXTEST command")
    yield master.load_ir(master.EXTEST)

    assert dut.tap_ioconn0__core__i == 0
    assert dut.tap_ioconn1__pad__o == 1
    assert dut.tap_ioconn2__pad__o == 0
    assert dut.tap_ioconn2__pad__oe == 0
    assert dut.tap_ioconn3__core__i == 1
    assert dut.tap_ioconn3__pad__o == 1
    assert dut.tap_ioconn3__pad__oe == 0

    data_in.binstr = "1011001"
    dut._log.info("  input data {}".format(data_in.binstr))
    
    # Set the ios pins
    dut.tap_ioconn0__pad__i = 0
    dut.tap_ioconn1__core__o = 1
    dut.tap_ioconn2__core__o = 0
    dut.tap_ioconn2__core__oe = 0
    dut.tap_ioconn3__pad__i = 1
    dut.tap_ioconn3__core__o = 1
    dut.tap_ioconn3__core__oe = 0
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "0100110")

    assert dut.tap_ioconn0__core__i == 1
    assert dut.tap_ioconn1__pad__o == 0
    assert dut.tap_ioconn2__pad__o == 1
    assert dut.tap_ioconn2__pad__oe == 1
    assert dut.tap_ioconn3__core__i == 0
    assert dut.tap_ioconn3__pad__o == 0
    assert dut.tap_ioconn3__pad__oe == 1

    yield master.reset()

    assert dut.tap_ioconn0__core__i == 0
    assert dut.tap_ioconn1__pad__o == 1
    assert dut.tap_ioconn2__pad__o == 0
    assert dut.tap_ioconn2__pad__oe == 0
    assert dut.tap_ioconn3__core__i == 1
    assert dut.tap_ioconn3__pad__o == 1
    assert dut.tap_ioconn3__pad__oe == 0


