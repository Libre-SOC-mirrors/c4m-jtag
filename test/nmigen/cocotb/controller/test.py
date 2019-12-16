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

    data_in.binstr = "011000"
    dut._log.info("  preloading data {}".format(data_in.binstr))

    # Set the ios pins
    dut.top_coreo = 2
    dut.top_coreoe = 0
    dut.top_padi = 1
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "100010")


    dut._log.info("Load EXTEST command")
    yield master.load_ir(master.EXTEST)

    data_in.binstr = "100111"
    dut._log.info("  input data {}".format(data_in.binstr))
    
    # Set the ios pins
    dut.top_coreo = 1
    dut.top_coreoe = 3
    dut.top_padi = 2
    yield master.shift_data(data_in)
    dut._log.info("  output: {}".format(master.result.binstr))
    assert(master.result.binstr == "011101")

    dut._log.info("Do a capture of the last loaded data")
    yield master.shift_data([])

