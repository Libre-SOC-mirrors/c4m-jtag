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
    
    -- JTAG state
    STATE:      in TAPSTATE_TYPE;
    NEXT_STATE: in TAPSTATE_TYPE;
    IRSTATE:    in std_logic;

    -- instruction register
    IR:         out std_logic_vector(IR_WIDTH-1 downto 0)
  );
end c4m_jtag_irblock;

architecture rtl of c4m_jtag_irblock is
  signal SHIFT_IR:      std_logic_vector(IR_WIDTH-1 downto 0);

  constant CMD_IDCODE:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_idcode(IR_WIDTH);
begin
  process (TCK, STATE)
  begin
    if STATE = TestLogicReset then
        SHIFT_IR <= (others => '0');
        IR <= CMD_IDCODE;
    elsif rising_edge(TCK) then
      if IRSTATE = '1' then
        case STATE is
          when Capture =>
            SHIFT_IR(1) <= '0';
            SHIFT_IR(0) <= '1';

          when Shift =>
            SHIFT_IR(IR_WIDTH-2 downto 0) <= SHIFT_IR(IR_WIDTH-1 downto 1);
            SHIFT_IR(IR_WIDTH-1) <= TDI;

          when Update =>
            IR <= SHIFT_IR;

          when others =>
            null;
        end case;
      end if;
    end if;
  end process;

  TDO <= SHIFT_IR(0) when STATE = Shift and IRSTATE = '1' else
         'Z';
end rtl;
