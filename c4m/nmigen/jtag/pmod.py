from nmigen.build import *

__all__ = [
    "PmodJTAGResource",
]


def PmodJTAGResource(*args, pmod_name="pmod", pmod_number, attrs=None,
                     master=False, reset=False):
    """Get a resource for a JTAG pins on a pmod.

    The pins are configured in such a way that the master pmod jtag can
    be connected to the tap pmod with a straight cable.

    Args:
        *args: either number or name, number.
        pmod_name (str): name of the pmod connector; default = "pmod"
        pmod_number (int): number of pmod connector
        attrs (Attrs): attributes for the ``Resource``
        master (bool): wether if this a master interface
        reset (bool): wether to include a reset signal
    """
    if master:
        mosi = "o"
        miso = "i"
        tdo_pin = "3"
        tdi_pin = "4"
    else:
        mosi = "i"
        miso = "o"
        tdo_pin = "4"
        tdi_pin = "3"
    conn = (pmod_name, pmod_number)

    ios = [
        Subsignal("tck", Pins("1", dir=mosi, conn=conn)),
        Subsignal("tms", Pins("2", dir=mosi, conn=conn)),
        Subsignal("tdo", Pins(tdo_pin, dir="o", conn=conn)),
        Subsignal("tdi", Pins(tdi_pin, dir="i", conn=conn)),
    ]
    if reset:
        ios.append(Subsignal("trst", PinsN("7", dir=mosi, conn=conn)))
    if attrs is not None:
        ios.append(attrs)

    return Resource.family(*args, default_name="jtag", ios=ios)
