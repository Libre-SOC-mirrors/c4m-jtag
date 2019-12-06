from modgrammar import *

grammar_whitespace_mode = 'explicit'
grammar_whitespace = WS_NOEOL

class SVFEol(Grammar):
    grammar = (OPTIONAL(SPACE), EOL)
    grammar_collapse = True

class SemicolonEol(Grammar):
    grammar = (OPTIONAL(SPACE), L(";"), SVFEol)
    grammar_collapse = True

class Integer(Grammar):
    grammar = WORD("0-9")
    grammar_collapse = True

class Float(Grammar):
    grammar = (Integer, (L("."), OPTIONAL(Integer)), OPTIONAL(L("E"), Integer))

class Hexadecimal(Grammar):
    grammar = (L("("), WORD("0-9A-F"), L(")"))
    grammar_collapse = True

class StableState(Grammar):
    grammar = (L("IRPAUSE") | L("DRPAUSE") | L("RESET") | L("IDLE"))
    grammar_collapse = True


class ScanSpec(Grammar):
    """The specification of Scan In/Scan out data"""
    grammar = (SPACE, Integer, SPACE,
               OPTIONAL(L("TDI"), OPTIONAL(SPACE), Hexadecimal),
               OPTIONAL(OPTIONAL(SPACE), L("TDO"), OPTIONAL(SPACE), Hexadecimal),
               OPTIONAL(OPTIONAL(SPACE), L("MASK"), OPTIONAL(SPACE), Hexadecimal),
               OPTIONAL(OPTIONAL(SPACE), L("SMASK"), OPTIONAL(SPACE), Hexadecimal)
              )
    grammar_collapse = True


class EmptyLine(Grammar):
    grammar = SVFEol

class Comment(Grammar):
    grammar = (L("!"), REST_OF_LINE, SVFEol)

class EndDR(Grammar):
    grammar = (L("ENDDR"), SPACE, StableState, SemicolonEol)

class EndIR(Grammar):
    grammar = (L("ENDIR"), SPACE, StableState, SemicolonEol)

class Frequency(Grammar):
    grammar = (L("FREQUENCY"), OPTIONAL(SPACE, Float, OPTIONAL(SPACE), L("HZ")), OPTIONAL(SPACE), SemicolonEol)

class HDR(Grammar):
    grammar = (L("HDR"), ScanSpec, SemicolonEol)

class HIR(Grammar):
    grammar = (L("HIR"), ScanSpec, SemicolonEol)

#TODO: PIO, PIOMAP

class Runtest(Grammar):
    grammar = (
        L("RUNTEST"),
        OPTIONAL(SPACE, StableState),
        OPTIONAL(SPACE, Integer, OPTIONAL(SPACE), (L("TCK") | L("SCK"))),
        OPTIONAL(SPACE, Float, OPTIONAL(SPACE), L("SEC")),
        OPTIONAL(SPACE, L("MAXIMUM"), SPACE, Float, OPTIONAL(SPACE), L("SEC")),
        OPTIONAL(SPACE, L("ENDSTATE"), SPACE, StableState),
        SemicolonEol
    )

class SDR(Grammar):
    grammar = (L("SDR"), ScanSpec, SemicolonEol)

class SIR(Grammar):
    grammar = (L("SIR"), ScanSpec, SemicolonEol)

class State(Grammar):
    # TODO: Path to reach state
    grammar = (L("STATE"), SPACE, StableState, SemicolonEol)

class TDR(Grammar):
    grammar = (L("TDR"), ScanSpec, SemicolonEol)

class TIR(Grammar):
    grammar = (L("TIR"), ScanSpec, SemicolonEol)

class Trst(Grammar):
    grammar = (L("TRST"), SPACE, (L("ON") | L("OFF") | L("Z") | L("ABSENT")), SemicolonEol)


class SVFFile(Grammar):
    grammar = ONE_OR_MORE(EmptyLine | Comment | Trst | EndDR | EndIR | SIR | SDR | Runtest | State)
