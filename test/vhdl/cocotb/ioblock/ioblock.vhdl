library ieee;
use ieee.std_logic_1164.all;

use work.c4m_jtag.all;

package ioblock_pkg is
  constant IOTYPES: IOTYPE_VECTOR(0 to 3) := (
    0 => IO_IN,
    1 => IO_OUT,
    2 => IO_OUT3,
    3 => IO_INOUT3
  );
  constant IR_WIDTH: integer := 2;
end package ioblock_pkg;


library ieee;
use ieee.std_logic_1164.all;

use work.c4m_jtag.all;
use work.ioblock_pkg.all;

entity ioblock is
  port (
    TCK:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TDO_EN:     out std_logic;

    IR:         in std_logic_vector(IR_WIDTH-1  downto 0);

    CAPTURE:    in std_logic;    
    SHIFT:      in std_logic;
    UPDATE:     in std_logic;

    CORE_OUT:   in std_logic_vector(IOTYPES'range);
    CORE_IN:    out std_logic_vector(IOTYPES'range);
    CORE_EN:    in std_logic_vector(IOTYPES'range);

    PAD_OUT:    out std_logic_vector(IOTYPES'range);
    PAD_IN:     in std_logic_vector(IOTYPES'range);
    PAD_EN:     out std_logic_vector(IOTYPES'range)
  );
end entity ioblock;

architecture rtl of ioblock is
begin
  blck: c4m_jtag_ioblock
    generic map (
      IR_WIDTH => IR_WIDTH,
      IOTYPES => IOTYPES
    )
    port map (
      TCK => TCK,
      TDI => TDI,
      TDO => TDO,
      TDO_EN => TDO_EN,
      IR => IR,
      CAPTURE => CAPTURE,
      SHIFT => SHIFT,    
      UPDATE => UPDATE,
      CORE_OUT => CORE_OUT,
      CORE_IN => CORE_IN,
      CORE_EN => CORE_EN,
      PAD_OUT => PAD_OUT,
      PAD_IN => PAD_IN,
      PAD_EN => PAD_EN
    );
end architecture rtl;
