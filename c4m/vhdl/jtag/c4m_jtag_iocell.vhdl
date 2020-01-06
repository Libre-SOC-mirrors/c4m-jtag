-- An JTAG boundary scan for bidirectional I/O

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_iocell is
  generic (
    IOTYPE:     IOTYPE_TYPE
  );
  port (
    -- core connections
    CORE_IN:    out std_logic;
    CORE_OUT:   in std_logic;
    CORE_EN:    in std_logic;

    -- pad connections
    PAD_IN:     in std_logic;
    PAD_OUT:    out std_logic;
    PAD_EN:     out std_logic;

    -- BD shift register
    BDSR_IN:    in std_logic;
    BDSR_OUT:   out std_logic;

      -- Mode of I/O cell
    IOMODE:     in SRIOMODE_TYPE;
    SAMPLEMODE: in SRSAMPLEMODE_TYPE;
    TCK:        in std_logic
  );
end c4m_jtag_iocell;

architecture rtl of c4m_jtag_iocell is
  signal SR_IOIN: std_logic;
  signal SR_IOOUT: std_logic;
  signal SR_IOEN: std_logic;
  signal SR_IOIN_next: std_logic;
  signal SR_IOOUT_next: std_logic;
  signal SR_IOEN_next: std_logic;

  signal CORE_IN_BD: std_logic;
  signal PAD_OUT_BD: std_logic;
  signal PAD_EN_BD: std_logic;
begin
  --
  -- CORE_* and PAD_* signals
  --
  INPUT_gen: if IOTYPE = IO_IN or IOTYPE = IO_INOUT3 generate
    with IOMODE select
    CORE_IN <=
      PAD_IN when SR_Through | SR_Z,
      PAD_IN when SR_2Pad,
      CORE_IN_BD when SR_2Core | SR_2PadCore,
      'X' when others;
  end generate INPUT_gen;
  NOINPUT_gen: if IOTYPE /= IO_IN and IOTYPE /= IO_INOUT3 generate
    CORE_IN <= 'X';
  end generate NOINPUT_gen;

  OUTPUT_gen: if IOTYPE /= IO_IN generate
    with IOMODE select
    PAD_OUT <=
      CORE_OUT when SR_Through,
      PAD_OUT_BD when SR_2Pad | SR_2PadCore,
      '0' when SR_2Core | SR_Z,
      'X' when others;
  end generate OUTPUT_gen;
  NOOUTPUT_gen: if IOTYPE = IO_IN generate
    PAD_OUT <= 'X';
  end generate NOOUTPUT_gen;

  ENABLE_gen: if IOTYPE = IO_OUT3 or IOTYPE = IO_INOUT3 generate
    with IOMODE select
    PAD_EN <=
      CORE_EN when SR_Through,
      PAD_EN_BD when SR_2Pad | SR_2PadCore,
      '0' when SR_2Core | SR_Z,
      'X' when others;
  end generate ENABLE_gen;
  NOENABLE_gen: if IOTYPE /= IO_OUT3 and IOTYPE /= IO_INOUT3 generate
    PAD_EN <= 'X';
  end generate NOENABLE_gen;


  --
  -- SR_* signals
  --
  IOIN_WITHIN_gen: if IOTYPE = IO_IN or IOTYPE = IO_INOUT3 generate
    with SAMPLEMODE select
      SR_IOIN_next <=
        PAD_IN when SR_Sample,
        BDSR_IN when SR_Shift,
        SR_IOIN when others;
  end generate IOIN_WITHIN_gen;
  IOIN_NOIN_gen: if IOTYPE /= IO_IN and IOTYPE /= IO_INOUT3 generate
    SR_IOIN_next <= 'X';
  end generate IOIN_NOIN_gen;

  IOOUT_NOINWITHOUT_gen: if IOTYPE = IO_OUT or IOTYPE = IO_OUT3 generate
    with SAMPLEMODE select
      SR_IOOUT_next <=
        CORE_OUT when SR_Sample,
        BDSR_IN when SR_Shift,
        SR_IOOUT when others;
  end generate IOOUT_NOINWITHOUT_gen;
  IOOUT_WITHINOUT_gen: if IOTYPE = IO_INOUT3 generate
    with SAMPLEMODE select
      SR_IOOUT_next <=
        CORE_OUT when SR_Sample,
        SR_IOIN when SR_Shift,
        SR_IOOUT when others;
  end generate IOOUT_WITHINOUT_gen;
  IOOUT_NOOUT_gen: if IOTYPE = IO_IN generate
    SR_IOOUT_next <= 'X';
  end generate IOOUT_NOOUT_gen;

  IOEN_WITHOUT3_gen: if IOTYPE = IO_OUT3 or IOTYPE = IO_INOUT3 generate
    with SAMPLEMODE select
      SR_IOEN_next <=
        CORE_EN when SR_Sample,
        SR_IOOUT when SR_Shift,
        SR_IOEN when others;
  end generate IOEN_WITHOUT3_gen;
  IOEN_NOOUT3_gen: if IOTYPE /= IO_OUT3 and IOTYPE /= IO_INOUT3 generate
    SR_IOEN_next <= 'X';
  end generate IOEN_NOOUT3_gen;

  process (TCK)
  begin
    -- Sampling of inputs and shifting of boundary scan SR needs to be done on
    -- rising edge of TCK.
    if rising_edge(TCK) then
      SR_IOIN <= SR_IOIN_next;
      SR_IOOUT <= SR_IOOUT_next;
      SR_IOEN <= SR_IOEN_next;
    end if;
    
    -- Update of output from boundary scan SR needs to be done on falling edge
    -- of TCK
    if falling_edge(TCK) and SAMPLEMODE = SR_Update then
      CORE_IN_BD <= SR_IOIN;
      PAD_OUT_BD <= SR_IOOUT;
      PAD_EN_BD <= SR_IOEN;
    end if;
  end process;


  --
  -- BDSR_OUT signal
  --
  BDSROUT_NOOUT_gen: if IOTYPE = IO_IN generate
    BDSR_OUT <= SR_IOIN;
  end generate BDSROUT_NOOUT_gen;
  BDSROUT_WITHOUT_gen: if IOTYPE = IO_OUT generate
    BDSR_OUT <= SR_IOOUT;
  end generate BDSROUT_WITHOUT_gen;
  BDSROUT_WITHOUT3_gen: if IOTYPE = IO_OUT3 or IOTYPE = IO_INOUT3 generate
    BDSR_OUT <= SR_IOEN;
  end generate BDSROUT_WITHOUT3_gen;
end rtl;
