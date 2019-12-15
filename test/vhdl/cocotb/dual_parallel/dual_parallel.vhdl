-- Top cell with two instantiations of the tap_controller with parallel scan chains

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity dual_parallel is
  port (
    -- Instance 1
    -- ==========
    -- JTAG
    I1_TCK:     in std_logic;
    I1_TMS:     in std_logic;
    I1_TDI:     in std_logic;
    I1_TDO:     out std_logic;
    I1_TRST_N:  in std_logic;

    -- Instance 2
    -- ==========
    -- JTAG
    I2_TCK:     in std_logic;
    I2_TMS:     in std_logic;
    I2_TDI:     in std_logic;
    I2_TDO:     out std_logic;
    I2_TRST_N:  in std_logic
  );
end dual_parallel;

architecture rtl of dual_parallel is
  signal I1_PAD_IN:     std_logic;
  signal I1_PAD_EN:     std_logic;
  signal I1_PAD_OUT:    std_logic;
  signal I2_PAD_IN:     std_logic;
  signal I2_PAD_EN:     std_logic;
  signal I2_PAD_OUT:    std_logic;
begin
  CTRL1: c4m_jtag_tap_controller
    port map (
      TCK => I1_TCK,
      TMS => I1_TMS,
      TDI => I1_TDI,
      TDO => I1_TDO,
      TRST_N => I1_TRST_N,
      RESET => open,
      CAPTURE => open,
      SHIFT => open,
      UPDATE => open,
      IR => open,
      CORE_IN => open,
      CORE_EN => "1",
      CORE_OUT => "1",
      PAD_IN(0) => I1_PAD_IN,
      PAD_EN(0) => I1_PAD_EN,
      PAD_OUT(0) => I1_PAD_OUT
    );

  CTRL2: c4m_jtag_tap_controller
    port map (
      TCK => I2_TCK,
      TMS => I2_TMS,
      TDI => I2_TDI,
      TDO => I2_TDO,
      TRST_N => I2_TRST_N,
      RESET => open,
      CAPTURE => open,
      SHIFT => open,
      UPDATE => open,
      IR => open,
      CORE_IN => open,
      CORE_EN => "1",
      CORE_OUT => "0",
      PAD_IN(0) => I2_PAD_IN,
      PAD_EN(0) => I2_PAD_EN,
      PAD_OUT(0) => I2_PAD_OUT
    );

  I1_PAD_IN <= I2_PAD_OUT when I2_PAD_EN = '1' else
               'Z';
  I2_PAD_IN <= I1_PAD_OUT when I1_PAD_EN = '1' else
               'Z';
end rtl;
