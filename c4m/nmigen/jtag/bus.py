from nmigen import *
from nmigen.hdl.rec import Direction

class Interface(Record):
    """JTAG Interface.

    Parameters
    ----------
    with_reset : bool, default=False
        wether to include trst field; if this field is not present a JTAG master
        should not rely on this pin for resetting a TAP.
    """
    def __init__(self, *, with_reset=False, name=None, src_loc_at=0):
        layout = [
            ("tck", 1, Direction.NONE),
            ("tms", 1, Direction.NONE),
            ("tdo", 1, Direction.FANOUT),
            ("tdi", 1, Direction.FANIN),
        ]
        if with_reset:
            layout.append(
                ("trst", 1, Direction.FANOUT)
            )
        super().__init__(layout, name=name, src_loc_at=src_loc_at+1)


class Chain(Elaboratable):
    """A chain of JTAG interfaces.

    Parameters
    ----------
    buses : iterable of :class:`Interface`, default=[]
        Initial value of the buses in the chain.
    with_reset : bool, default=False
        Wether the generated bus has a reset pin. If value is True all buses in
        the chain also have to have a reset signal

    Attributes
    ----------
    bus : :class:`Interface`
    """
    def __init__(self, *, with_reset=False, buses=[], name=None, src_loc_at=0):
        for bus in buses:
            if not isinstance(bus, Interface):
                raise ValueError("Object in buses that is not a JTAG Interface")
            if with_reset and not hasattr(bus, "trst"):
                raise ValueError("JTAG bus in buses without a reset signal")

        kwargs = {
            "with_reset": with_reset,
            "src_loc_at": src_loc_at + 1,
        }
        if name is not None:
            kwargs["name"] = name + "_bus"
        self.bus = Interface(**kwargs)

        self._buses = buses

    def add(bus):
        """Add a bus to the chain"""

        if not isinstance(bus, Interface):
            raise ValueError("bus in not a JTAG Interface")
        if hasattr(self.bus, "trst") and not hasattr(bus, "trst"):
            raise ValueError("bus needs to have a reset signal")
        self._buses.append(bus)

    def elaborate(self, platform):
        with_reset = hasattr(self.bus, "trst")

        m = Module()

        # Connect first and last
        m.d.comb += [
            self._buses[0].tdi.eq(self.bus.tdo),
            self.bus.tdi.eq(self._buses[-1].tdo),
        ]
        for i in range(len(self._buses)):
            if i < len(self._buses) - 1:
                m.d.comb += self._buses[i+1].tdi.eq(self._buses[i].tdo)
            if with_reset:
                m.d.comb += self._buses[i].trst.eq(self.bus.trst)

        return m
