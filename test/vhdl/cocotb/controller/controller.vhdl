library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

package controller_pkg is
  constant IOTYPES:     IOTYPE_VECTOR(0 to 3) := (
    0 => IO_IN,
    1 => IO_OUT,
    2 => IO_OUT3,
    3 => IO_INOUT3
  );
end package controller_pkg;

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;
use work.controller_pkg.ALL;

entity controller is
  port (
    -- The TAP signals
    TCK:        in std_logic;
    TMS:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TRST_N:     in std_logic;

    -- The Instruction Register
    IR:         out std_logic_vector(1 downto 0);

    -- The FSM state indicators
    RESET:      out std_logic;
    CAPTURE:    out std_logic;
    SHIFT:      out std_logic;
    UPDATE:     out std_logic;

    -- The I/O access ports
    CORE_IN:    out std_logic_vector(IOTYPES'range);
    CORE_EN:    in std_logic_vector(IOTYPES'range);
    CORE_OUT:   in std_logic_vector(IOTYPES'range);

    -- The pad connections
    PAD_IN:     in std_logic_vector(IOTYPES'range);
    PAD_EN:     out std_logic_vector(IOTYPES'range);
    PAD_OUT:    out std_logic_vector(IOTYPES'range)
  );
end controller;

architecture rtl of controller is
begin
  ctrl: c4m_jtag_tap_controller
    generic map (
      DEBUG => true,
      IOTYPES => IOTYPES
    )
    port map (
      TCK => TCK,
      TMS => TMS,
      TDI => TDI,
      TDO => TDO,
      TRST_N => TRST_N,
      IR => IR,
      RESET => RESET,
      CAPTURE => CAPTURE,
      SHIFT => SHIFT,
      UPDATE => UPDATE,
      CORE_IN => CORE_IN,
      CORE_EN => CORE_EN,
      CORE_OUT => CORE_OUT,
      PAD_IN => PAD_IN,
      PAD_EN => PAD_EN,
      PAD_OUT => PAD_OUT
    );
end architecture rtl;
