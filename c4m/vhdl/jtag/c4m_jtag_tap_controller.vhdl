-- A JTAG complient tap controller implementation
-- This is implemented based on the IEEE 1149.1 standard

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_tap_controller is
  generic (
    DEBUG:              boolean := false;

    IR_WIDTH:           integer := 2;
    IOS:                integer := 1;

    MANUFACTURER:       std_logic_vector(10 downto 0) := "10001111111";
    PART_NUMBER:        std_logic_vector(15 downto 0) := "0000000000000001";
    VERSION:            std_logic_vector(3 downto 0) := "0000"
  );
  port (
    -- The TAP signals
    TCK:        in std_logic;
    TMS:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TRST_N:     in std_logic;

    -- The Instruction Register
    IR:         out std_logic_vector(IR_WIDTH-1 downto 0);

    -- The FSM state indicators
    RESET:      out std_logic;
    CAPTURE:    out std_logic;
    SHIFT:      out std_logic;
    UPDATE:     out std_logic;

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
  signal S_RESET:       std_logic;
  signal S_ISIR:        std_logic;
  signal S_ISDR:        std_logic;
  signal S_CAPTURE:     std_logic;
  signal S_SHIFT:       std_logic;
  signal S_UPDATE:      std_logic;
  signal S_IR:          std_logic_vector(IR_WIDTH-1 downto 0);

  signal IR_TDO:        std_logic;
  signal IR_TDO_EN:     std_logic;
  signal ID_TDO:        std_logic;
  signal ID_TDO_EN:     std_logic;
  signal IO_TDO:        std_logic;
  signal IO_TDO_EN:     std_logic;
begin
  IR <= S_IR;
  RESET <= S_RESET;
  CAPTURE <= S_CAPTURE and S_ISDR;
  SHIFT <= S_SHIFT and S_ISDR;
  UPDATE <= S_UPDATE and S_ISDR;

  -- JTAG state machine
  FSM:  c4m_jtag_tap_fsm
    port map (
      TCK => TCK,
      TMS => TMS,
      TRST_N => TRST_N,
      RESET => S_RESET,
      ISIR => S_ISIR,
      ISDR => S_ISDR,
      CAPTURE => S_CAPTURE,
      SHIFT => S_SHIFT,
      UPDATE => S_UPDATE
    );

  -- The instruction register
  IRBLOCK: c4m_jtag_irblock
    generic map (
      IR_WIDTH => IR_WIDTH
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => IR_TDO,
      TDO_EN => IR_TDO_EN,
      IR => S_IR,
      RESET => S_RESET,
      CAPTURE => S_CAPTURE and S_ISIR,
      SHIFT => S_SHIFT and S_ISIR,
      UPDATE => S_UPDATE and S_ISIR
    );

  -- The ID
  IDBLOCK: c4m_jtag_idblock
    generic map (
      IR_WIDTH => IR_WIDTH,
      PART_NUMBER => PART_NUMBER,
      MANUFACTURER => MANUFACTURER,
      VERSION => VERSION
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => ID_TDO,
      TDO_EN => ID_TDO_EN,
      IR => S_IR,
      CAPTURE => S_CAPTURE and S_ISDR,
      SHIFT => S_SHIFT and S_ISDR,
      UPDATE => S_UPDATE and S_ISDR
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
      TDO => IO_TDO,
      TDO_EN => IO_TDO_EN,
      IR => S_IR,
      CAPTURE => S_CAPTURE and S_ISDR,
      SHIFT => S_SHIFT and S_ISDR,
      UPDATE => S_UPDATE and S_ISDR,
      CORE_OUT => CORE_OUT,
      CORE_IN => CORE_IN,
      CORE_EN => CORE_EN,
      PAD_OUT => PAD_OUT,
      PAD_IN => PAD_IN,
      PAD_EN => PAD_EN
    );

  TDO <= IR_TDO when IR_TDO_EN = '1' else
         ID_TDO when ID_TDO_EN = '1' else
         IO_TDO when IO_TDO_EN = '1' else
         '0';

  CHECK_EN: if DEBUG generate
    signal EN:  std_logic_vector(2 downto 0) := "000";
  begin
    EN <= IR_TDO_EN & ID_TDO_EN & IO_TDO_EN;
    assert EN = "000" or EN = "100" or EN = "010" or EN = "001"
      report "TDO conflict in c4m_jtag_tap_controller"
      severity ERROR;
  end generate CHECK_EN;
end rtl;


