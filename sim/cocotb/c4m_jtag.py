import cocotb
from cocotb.triggers import Timer
from cocotb.utils import get_sim_steps
from cocotb.binary import BinaryValue

class JTAG_Clock(object):
    """
    Class for the JTAG clock, run cycle by cycle
    """
    def __init__(self, signal, period):
        self.signal = signal
        self.t = Timer(period/4)

    @cocotb.coroutine
    def Cycle(self, cycles=1):
        """
        Do one or more cycles
        Cycle start in middle of 0 pulse of the clock
        """
        for i in range(cycles):
            self.signal <= 0
            yield self.t
            self.signal <= 1
            yield self.t
            yield self.t
            self.signal <= 0
            yield self.t

class JTAG_Master(object):
    """
    Class that will run JTAG commands, shift in and out data
    """
    #TODO: Handle a JTAG chain with more than one device

    def __init__(self, tck, tms, tdi, tdo, trst_n=None, clk_period=1000):
        self.tck = tck
        self.clkgen = JTAG_Clock(tck, clk_period)
        tck <= 0
        self.tms = tms
        tms <= 1
        self.tdi = tdi
        tdi <= 0
        self.tdo = tdo
        self.trst_n = trst_n
        trst_n <= 1
        self.period = Timer(clk_period)

        # Standard commands
        # TODO: make IR length configurable; now 2 is assumed
        self.BYPASS = [1, 1]
        self.IDCODE = [0, 1]
        self.SAMPLEPRELOAD = [1, 0]
        self.EXTEST = [0, 0]

        # After command we always leave the controller in reset or runidle state
        # If value is None we will always reset the interface
        self.state = None

        # The methods of this class are coroutines. The results will be stored
        # in the result field
        self.result = None

    @cocotb.coroutine
    def cycle_clock(self, cycles=1):
        if self.state == "Run" and self.tms == 1:
            self.state = "Scan"
        yield self.clkgen.Cycle(cycles)

    @cocotb.coroutine
    def reset(self):
        if not self.trst_n is None:
            # Enable reset signal for one clock period
            self.trst_n <= 0
            yield self.period
            self.trst_n <= 1
        else:
            # 5 cycles with tms on 1 should reset the JTAG TAP controller
            self.tms <= 1
            yield self.cycle_clock(5)

        self.state = "Reset"

        self.result = None

    @cocotb.coroutine
    def change_state(self, tms_list):
        """
        Put TAP in other state by giving a TMS sequence
        This function does not detect if one ends up in reset or run
        state afterwards, self.state has to be updated by caller
        if that is the case.
        """
        tms_copy = list(tms_list)
        while tms_copy:
            self.tms <= tms_copy.pop()
            yield self.cycle_clock()
        self.result = None

    @cocotb.coroutine
    def change_to_run(self):
        """
        Put TAP in RunTestIdle state
        self.result is bool and true if TAP went through reset state
        """
        isreset = False
        if self.state is None:
            yield self.reset()
        if self.state is "Reset":
            isreset = True
            self.tms <= 0
            yield self.cycle_clock()
            self.state = "Run"
        assert(self.state == "Run")
        self.result = isreset

    @cocotb.coroutine
    def load_ir(self, cmd):
        cmd_copy = list(cmd)
        result = BinaryValue(bits=len(cmd_copy))
        l_result = list()

        yield self.change_to_run()
        # Go to Capture/IR
        yield self.change_state([0, 1, 1])

        # Shift the two
        self.tms <= 0
        while cmd_copy:
            # In first iteration we enter SHIFT state and tdo is made active
            yield self.cycle_clock()
            # For the last iteration tdi will be shifted when entering next state
            self.tdi <= cmd_copy.pop()
            l_result.insert(0, str(self.tdo))

        # Go to RunTestIdle
        yield self.change_state([0, 1, 1])
        self.state = "Run"

    @cocotb.coroutine
    def idcode(self):
        """
        Get the IDCODE from the device
        result will contain the 32 bit IDCODE of the device
        """

        result = BinaryValue(bits=32)
        l_result = list()

        # Keep tdi 0 for the whole run
        self.tdi <= 0

        yield self.change_to_run()
        if not self.result:
            # If TAP was not reset we have to load IDCODE command
            yield self.load_ir(self.IDCODE)

        # Should be again in RUN state
        assert(self.state == "Run")

        # Go to Shift/DR
        yield self.change_state([0, 0, 1])

        # Enter Shift; run for 32 cycles
        self.tms <= 0
        for i in range(32):
            l_result.insert(0, str(self.tdo))
            yield self.cycle_clock()
        result.binstr = "".join(l_result)

        # Go to RunTestIdle
        yield self.change_state([0, 1, 1])
        self.state = "Run"

        self.result = result

    @cocotb.coroutine
    def shift_data(self, data_in):
        """
        Shift data in through the JTAG and capture the output
        Input can be of type BinaryValue or an iterable value of 0 and 1s.
        Last bit will be shifted in first.
        result will contain the sample TDO with the same number of bits as the input
        """
        if isinstance(data_in, BinaryValue):
            data_copy = [int(c) for c in data_in.binstr]
        else:
            data_copy = list(data_in)
        result = BinaryValue()
        l_result = list()

        yield self.change_to_run()
        # Go to Capture/DR
        yield self.change_state([0, 1])

        # Shift data through
        self.tms <= 0
        while data_copy:
            yield self.cycle_clock()
            self.tdi <= data_copy.pop()
            l_result.insert(0, str(self.tdo))
        result.binstr = "".join(l_result)

        # Go to RunTestIdle
        yield self.change_state([0, 1, 1])
        self.state = "Run"

        self.result = result
