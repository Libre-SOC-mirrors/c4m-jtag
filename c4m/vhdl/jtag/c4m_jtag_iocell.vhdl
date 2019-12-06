-- An JTAG boundary scan for bidirectional I/O

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_iocell is
  generic (
    IR_WIDTH:   integer := 2
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

  signal CORE_IN_BD: std_logic;
  signal PAD_OUT_BD: std_logic;
  signal PAD_EN_BD: std_logic;
begin
  with IOMODE select
  CORE_IN <=
    PAD_IN when SR_Through | SR_Z,
    PAD_IN when SR_2Pad,
    CORE_IN_BD when SR_2Core,
    'X' when others;

  with IOMODE select
  PAD_OUT <=
    CORE_OUT when SR_Through,
    PAD_OUT_BD when SR_2Pad,
    '0' when SR_2Core | SR_Z,  
    'X' when others;

  with IOMODE select
  PAD_EN <=
    CORE_EN when SR_Through,
    PAD_EN_BD when SR_2Pad,
    '0' when SR_2Core | SR_Z,
    'X' when others;

  process (TCK)
  begin
    -- Sampling of inputs and shifting of boundary scan SR needs to be done on
    -- rising edge of TCK
    if rising_edge(TCK) then
      case SAMPLEMODE is
        when SR_Sample =>
          SR_IOIN <= PAD_IN;
          SR_IOOUT <= CORE_OUT;
          SR_IOEN <= CORE_EN;

        when SR_Shift =>
          SR_IOIN <= BDSR_IN;
          SR_IOOUT <= SR_IOIN;
          SR_IOEN <= SR_IOOUT;

        when others =>
          null;
      end case;
    end if;
    
    -- Update of output from boundary scan SR needs to be done on falling edge
    -- of TCK
    if falling_edge(TCK) then
      case SAMPLEMODE is
        when SR_Update =>
          CORE_IN_BD <= SR_IOIN;
          PAD_OUT_BD <= SR_IOOUT;
          PAD_EN_BD <= SR_IOEN;
          
        when others =>
          null;
      end case;
    end if;
  end process;

  BDSR_OUT <= SR_IOEN;
end rtl;
