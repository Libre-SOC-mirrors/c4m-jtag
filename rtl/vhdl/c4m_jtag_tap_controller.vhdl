-- A JTAG complient tap controller implementation
-- This is implemented based on the IEEE 1149.1 standard

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_tap_controller is
  generic (
    IR_WIDTH:   integer := 2;
    IOS:        integer := 1;

    VERSION:    std_logic_vector(3 downto 0)
  );
  port (
    -- The TAP signals
    TCK:        in std_logic;
    TMS:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TRST_N:     in std_logic;

    -- The FSM state indicators
    STATE:      out TAPSTATE_TYPE;
    NEXT_STATE: out TAPSTATE_TYPE;
    DRSTATE:    out std_logic;

    -- The Instruction Register
    IR:         out std_logic_vector(IR_WIDTH-1 downto 0);

    -- The I/O access ports
    CORE_IN:    out std_logic_vector(IOS-1 downto 0);
    CORE_EN:    in std_logic_vector(IOS-1 downto 0);
    CORE_OUT:   in std_logic_vector(IOS-1 downto 0);

    -- The pad connections
    PAD_IN:     in std_logic_vector(IOS-1 downto 0);
    PAD_EN:     out std_logic_vector(IOS-1 downto 0);
    PAD_OUT:    out std_logic_vector(IOS-1 downto 0)
  );
end c4m_jtag_tap_controller;

architecture rtl of c4m_jtag_tap_controller is
  signal S_STATE:       TAPSTATE_TYPE;
  signal S_NEXT_STATE:  TAPSTATE_TYPE;
  signal S_IRSTATE:       std_logic;
  signal S_DRSTATE:       std_logic;
  signal S_IR:          std_logic_vector(IR_WIDTH-1 downto 0);

  -- TODO: Automate PART_NUMBER generation
  constant PART_NUMBER: std_logic_vector(15 downto 0) := "0000000010001001";
  -- TODO: Get manufacturer ID
  constant MANUFACTURER: std_logic_vector(10 downto 0) := "00000000000";
begin
  STATE <= S_STATE;
  NEXT_STATE <= S_NEXT_STATE;
  DRSTATE <= S_DRSTATE;
  IR <= S_IR;

  -- JTAG state machine
  FSM:  c4m_jtag_tap_fsm
    port map (
      TCK => TCK,
      TMS => TMS,
      TRST_N => TRST_N,
      STATE => S_STATE,
      NEXT_STATE => S_NEXT_STATE,
      DRSTATE => S_DRSTATE,
      IRSTATE => S_IRSTATE
    );

  -- The instruction register
  IRBLOCK: c4m_jtag_irblock
    generic map (
      IR_WIDTH => IR_WIDTH
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => TDO,
      STATE => S_STATE,
      NEXT_STATE => S_NEXT_STATE,
      IRSTATE => S_IRSTATE,
      IR => S_IR
    );

  -- The ID
  IDBLOCK: c4m_jtag_idblock
    generic map (
      IR_WIDTH => IR_WIDTH,
      PART_NUMBER => PART_NUMBER,
      MANUFACTURER => MANUFACTURER
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => TDO,
      STATE => S_STATE,
      NEXT_STATE => S_NEXT_STATE,
      DRSTATE => S_DRSTATE,
      IR => S_IR
    );
  
  -- The IOS
  IOBLOCK: c4m_jtag_ioblock
    generic map (
      IR_WIDTH => IR_WIDTH,
      IOS => IOS
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => TDO,
      STATE => S_STATE,
      NEXT_STATE => S_NEXT_STATE,
      DRSTATE => S_DRSTATE,
      IR => S_IR,
      CORE_OUT => CORE_OUT,
      CORE_IN => CORE_IN,
      CORE_EN => CORE_EN,
      PAD_OUT => PAD_OUT,
      PAD_IN => PAD_IN,
      PAD_EN => PAD_EN
    );
end rtl;


