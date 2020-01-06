import cocotb
from cocotb.utils import get_sim_steps
from cocotb.binary import BinaryValue
from cocotb.triggers import Timer

def report_bdsr(dut):
    for handle in dut.blck:
        if handle._name.startswith("iogen"):
            for handle2 in handle:
                if handle2._name == "iocell":
                    values = {}
                    for handle3 in handle2:
                        if handle3._name in ("bdsr_in", "bdsr_out", "sr_ioin", "sr_ioout", "sr_ioen"):
                            values[handle3._name] = handle3.value.binstr
                    dut._log.info("{}: {!r}".format(handle2._path, values))

@cocotb.test()
def test01_boundaryscan(dut):
    """
    Check initialization
    """
    dut.ir = 0
    dut.tck = 0
    dut.tdi = 1
    dut.capture = 0
    dut.shift = 0
    dut.update = 0

    # Boundary scan: IN > OUT > OUT3 > INOUT3
    # Length: 1 + 1 + 2 + 3 = 7

    yield Timer(1)

    report_bdsr(dut)

    assert dut.core_in.value.binstr == "UXXU"
    assert dut.pad_out.value.binstr == "XUUU"
    assert dut.pad_en.value.binstr == "XXUU"

    dut.ir = BinaryValue("10") # SAMPLEPRELOAD
    dut.core_out = BinaryValue("0000")
    dut.core_en = BinaryValue("0000")
    dut.pad_in = BinaryValue("0000")
    yield Timer(1)

    assert dut.core_in.value.binstr == "0XX0"
    assert dut.pad_out.value.binstr == "X000"
    assert dut.pad_en.value.binstr == "XX00"

    dut.capture = 1
    yield Timer(1)
    dut.tck = 1
    yield Timer(1)
    dut.capture = 0
    dut.tck = 0
    yield Timer(1)

    assert dut.core_in.value.binstr == "0XX0"
    assert dut.pad_out.value.binstr == "X000"
    assert dut.pad_en.value.binstr == "XX00"

    dut.shift = 1
    yield Timer(1)
    for i in range(7):
        dut._log.info("Cycle {}".format(i))
        report_bdsr(dut)
        assert dut.tdo.value.binstr == "0"
        dut.tck = 1
        yield Timer(1)
        dut.tck = 0
        yield Timer(1)
    dut._log.info("Cycle 7")
    report_bdsr(dut)
    assert dut.tdo.value.binstr == "1"

    dut.shift = 0
    dut.update = 1
    yield Timer(1)
    dut.tck = 1
    yield Timer(1)
    dut.update = 0
    dut.tck = 0
    yield Timer(1)

    assert dut.core_in.value.binstr == "0XX0"
    assert dut.pad_out.value.binstr == "X000"
    assert dut.pad_en.value.binstr == "XX00"

    dut.ir = BinaryValue("00") # EXTEST
    yield Timer(1)
    
    assert dut.core_in.value.binstr == "0XX0"
    assert dut.pad_out.value.binstr == "X111"
    assert dut.pad_en.value.binstr == "XX11"
