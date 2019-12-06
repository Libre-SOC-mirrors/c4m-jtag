import cocotb
from cocotb.utils import get_sim_steps

from c4m_jtag import JTAG_Master

@cocotb.test()
def test01_dual(dut):
    """
    Test the IDCODE command
    """

    # TODO: Allow parallel operation of the JTAG chains

    # Run @ 1MHz
    clk_period = get_sim_steps(1, "us")
    master1 = JTAG_Master(dut.i1_tck, dut.i1_tms, dut.i1_tdi, dut.i1_tdo, dut.i1_trst_n, clk_period)
    master2 = JTAG_Master(dut.i2_tck, dut.i2_tms, dut.i2_tdi, dut.i2_tdo, dut.i2_trst_n, clk_period)

    dut._log.info("Set command to SAMPLEPRELOAD")
    yield master1.load_ir(master1.SAMPLEPRELOAD)
    yield master2.load_ir(master2.SAMPLEPRELOAD)
    
    dut._log.info("Load data, scan out first sample")
    yield master1.shift_data([0, 0, 0])
    dut._log.info("  master1 scan_out: {}".format(master1.result.binstr))
    assert(master1.result.binstr == "011")
    yield master2.shift_data([1, 1, 1])
    dut._log.info("  master2 scan_out: {}".format(master2.result.binstr))
    assert(master2.result.binstr == "101")
    
    dut._log.info("Set command to EXTEST")
    yield master1.load_ir(master1.EXTEST)
    yield master2.load_ir(master2.EXTEST)

    dut._log.info("Second scan")
    yield master1.shift_data([0, 0, 0])
    dut._log.info("  master1 scan_out: {}".format(master1.result.binstr))
    assert(master1.result.binstr == "111")
    yield master2.shift_data([1, 1, 1])
    dut._log.info("  master2 scan_out: {}".format(master2.result.binstr))
    assert(master2.result.binstr == "Z01")
