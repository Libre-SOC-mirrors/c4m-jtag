import c4m_jtag_svfgrammar
import cocotb
from cocotb.binary import BinaryValue
from functools import singledispatch

def decodescanspec(node):
    length = int(str(node[2]))
    fstr = "{:0"+str(node[2])+"b}"

    g_tdi = node[4]
    g_tdo = node[5]
    g_mask = node[6]
    g_smask = node[7]

    if g_tdi is None:
        tdi = None
    else:
        tdi = BinaryValue(fstr.format(int(str(g_tdi[2]),16)), length)

    if g_tdo is None:
        tdo = None
    else:
        tdo = BinaryValue(fstr.format(int(str(g_tdo[3]),16)), length)

    if g_mask is None:
        mask = None
    else:
        mask = BinaryValue(fstr.format(int(str(g_mask[3]),16)), length)

    if g_smask is None:
        smask = None
    else:
        smask = BinaryValue(fstr.format(int(str(g_smask[3]),16)), length)

    return (length, tdi, tdo, mask, smask)


class SVF_Executor(object):
    @cocotb.coroutine
    def execute(self, node):
        """This is the generic method"""
        self._p("generic")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_NOP(self, node):
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_EndDR(self, node):
        self._p("EndDR ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_EndIR(self, node):
        self._p("EndIR ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_Frequency(self, node):
        self._p("Frequency ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_HDR(self, node):
        self._p("HDR ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_HIR(self, node):
        self._p("HIR ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_SDR(self, node):
        self._p("Executing SDR")
        (length, tdi, tdo, mask, smask) = decodescanspec(node)

        samelength = length == self._d_length
        self._d_length = length

        if tdi is None:
            if not samelength:
                raise(JTAGException("TDI needs to be specified when length of data changes"))
        else:
            self._d_tdi = tdi

        if mask is not None:
            self._d_mask = mask
        elif not samelength:
            self._d_mask = None

        if smask is not None:
            self._d_smask = smask
        elif not samelength:
            self._d_smask = None

        yield self.master.shift_data(self._d_tdi)
        if tdo is not None:
            if self._d_mask is not None:
                raise(JTAGException("MASK not supported for SDR"))
            assert(self.result == tdo)

    @cocotb.coroutine
    def _execute_SIR(self, node):
        (length, tdi, tdo, mask, smask) = decodescanspec(node)

        samelength = length == self._i_length
        self._i_length = length

        if tdi is None:
            if not samelength:
                raise(JTAGException("TDI needs to be specified when length of data changes"))
        else:
            self._i_tdi = tdi

        if mask is not None:
            self._i_mask = mask
        elif not samelength:
            self._i_mask = None

        if smask is not None:
            self._i_smask = smask
        elif not samelength:
            self._i_smask = None

        self._p("Executing SIR ({})".format(self._i_tdi.integer))

        yield self.master.load_ir(self._i_tdi)
        if tdo is not None:
            if self._i_mask is not None:
                raise(JTAGException("MASK not supported for SIR"))
            assert(self.result == tdo)
        

    @cocotb.coroutine
    def _execute_State(self, node):
        self._p("State")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_TDR(self, node):
        self._p("TDR")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_TIR(self, node):
        self._p("TIR")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_Trst(self, node):
        self._p("TRST ignored")
        if False: # Make coroutine work
            yield PythonTrigger()

    @cocotb.coroutine
    def _execute_Runtest(self, node):
        if node[1] is not None:
            raise(JTAGException("State specification for RUNTEST not supported"))
        # TODO: cycle the right number of clocks or wait the right time
        yield(self.master.change_state([0]))

    @cocotb.coroutine
    def _execute_SVFFile(self, node):
        self._p("Executing SVFFile")
        for statement in node.elements[0]:
            yield self.execute(statement)

    def __init__(self, master):
        # master is assumed to be a JTAG_Master class
        # it needs to support methods load_ir() and shift_data()
        self.master = master

        # Due to bug in Grammar definition all possible classes have to have
        # a dispatch entry otherwise an error will be raised.
        self.execute = singledispatch(self.execute)
        self.execute.register(c4m_jtag_svfgrammar.EmptyLine, self._execute_NOP)
        self.execute.register(c4m_jtag_svfgrammar.Comment, self._execute_NOP)
        self.execute.register(c4m_jtag_svfgrammar.EndDR, self._execute_EndDR)
        self.execute.register(c4m_jtag_svfgrammar.EndIR, self._execute_EndIR)
        self.execute.register(c4m_jtag_svfgrammar.Frequency, self._execute_Frequency)
        self.execute.register(c4m_jtag_svfgrammar.HDR, self._execute_HDR)
        self.execute.register(c4m_jtag_svfgrammar.HIR, self._execute_HIR)
        self.execute.register(c4m_jtag_svfgrammar.Runtest, self._execute_Runtest)
        self.execute.register(c4m_jtag_svfgrammar.SDR, self._execute_SDR)
        self.execute.register(c4m_jtag_svfgrammar.SIR, self._execute_SIR)
        self.execute.register(c4m_jtag_svfgrammar.State, self._execute_State)
        self.execute.register(c4m_jtag_svfgrammar.TDR, self._execute_TDR)
        self.execute.register(c4m_jtag_svfgrammar.TIR, self._execute_TIR)
        self.execute.register(c4m_jtag_svfgrammar.Trst, self._execute_Trst)
        self.execute.register(c4m_jtag_svfgrammar.SVFFile, self._execute_SVFFile)

        # Store the head and tail for the scan
        self._d_tdi = self._d_tdi_h = self._d_tdi_t = None
        self._d_tdo_h = self._d_tdo_t = None
        self._i_tdi = self._i_tdi_h = self._i_tdi_t = None
        self._i_tdo_h = self._i_tdo_t = None

        # Remember the masks; smasks are ignored and bits always considered as care, e.g right
        # value applied
        self._d_length = self._d_length_h = self._d_length_t = None
        self._d_mask = self._d_mask_h = self._d_mask_t = None
        self._d_smask = self._d_smask_h = self._d_smask_t = None
        self._i_length = self._i_length_h = self._i_length_t = None
        self._i_mask = self._i_mask_h = self._i_mask_t = None
        self._i_smask = self._i_smask_h = self._i_smask_t = None

    @cocotb.coroutine
    def run(self, cmds, p=print):
        self._p = p
        if isinstance(cmds, c4m_jtag_svfgrammar.SVFFile):
            yield self.execute(cmds)
        else:
            p = c4m_jtag_svfgrammar.SVFFile.parser()
            yield self.execute(p.parse_string(cmds))
