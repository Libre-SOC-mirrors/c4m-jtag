-- Handle the instruction register for the JTAG controller

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_irblock is
  generic (
    IR_WIDTH:   integer := 2
  );
  port (
    -- needed TAP signals
    TCK:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TDO_EN:     out std_logic := '0';

    -- instruction register
    IR:         out std_logic_vector(IR_WIDTH-1 downto 0);

    -- actions
    RESET:      in std_logic;
    CAPTURE:    in std_logic;
    SHIFT:      in std_logic;
    UPDATE:     in std_logic
  );
end c4m_jtag_irblock;

architecture rtl of c4m_jtag_irblock is
  signal SHIFT_IR:      std_logic_vector(IR_WIDTH-1 downto 0);

  constant CMD_IDCODE:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_idcode(IR_WIDTH);
begin
  process (TCK)
  begin
    if rising_edge(TCK) then
      if RESET = '1' then
        SHIFT_IR <= (others => '0');
        IR <= CMD_IDCODE;
      elsif CAPTURE = '1' then
        SHIFT_IR(1) <= '0';
        SHIFT_IR(0) <= '1';
      elsif SHIFT = '1' then
        SHIFT_IR(IR_WIDTH-2 downto 0) <= SHIFT_IR(IR_WIDTH-1 downto 1);
        SHIFT_IR(IR_WIDTH-1) <= TDI;
      elsif UPDATE = '1' then
        IR <= SHIFT_IR;
      end if;
    end if;
  end process;

  TDO <= SHIFT_IR(0) when SHIFT = '1' else
         'X';
  TDO_EN <= '1' when SHIFT = '1' else
            '0';
end rtl;
