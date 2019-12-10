-- The JTAG id and bypass handling block

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_idblock is
  generic (
    IR_WIDTH:           integer := 2;
    
    MANUFACTURER:       std_logic_vector(10 downto 0) := "10001111111";
    PART_NUMBER:        std_logic_vector(15 downto 0) := "0000000000000001";
    VERSION:            std_logic_vector(3 downto 0) := "0000"
  );
  port (
    -- needed TAP signals
    TCK:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TDO_EN:     out std_logic := '0';

    -- The instruction
    IR:         in std_logic_vector(IR_WIDTH-1 downto 0);

    -- actions
    CAPTURE:    in std_logic;
    SHIFT:      in std_logic;
    UPDATE:     in std_logic
  );
end c4m_jtag_idblock;

architecture rtl of c4m_jtag_idblock is
  constant IDCODE:      std_logic_vector(31 downto 0) := VERSION & PART_NUMBER & MANUFACTURER & "1";

  signal SR_ID:         std_logic_vector(31 downto 0);
  signal EN_TDO:        boolean;
  
  constant CMD_IDCODE:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_idcode(IR_WIDTH);
  constant CMD_BYPASS:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_bypass(IR_WIDTH);
begin
  process (TCK)
  begin
    if rising_edge(TCK) then
      if CAPTURE = '1' then
        SR_ID <= IDCODE;
      elsif SHIFT = '1' then
        if IR = CMD_IDCODE then
          SR_ID(30 downto 0) <= SR_ID(31 downto 1);
          SR_ID(31) <= TDI;
        elsif IR = CMD_BYPASS then
          SR_ID(0) <= TDI;
        end if;
      end if;
    end if;
  end process;

  TDO <= SR_ID(0) when EN_TDO else
         '0';
  EN_TDO <= SHIFT = '1' and (IR = CMD_IDCODE or IR = CMD_BYPASS);
  TDO_EN <= '1' when EN_TDO else
            '0';
end rtl;
