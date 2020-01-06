-- The block of io cells with JTAG boundary scan support

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_ioblock is
  generic (
    IR_WIDTH:   integer := 2;
    IOTYPES:    IOTYPE_VECTOR
  );
  port (
    -- needed TAP signals
    TCK:        in std_logic;
    TDI:        in std_logic;
    TDO:        out std_logic;
    TDO_EN:     out std_logic := '0';

    -- The instruction
    IR:         in std_logic_vector(IR_WIDTH-1 downto 0);

    -- What action to perform
    CAPTURE:    in std_logic;
    SHIFT:      in std_logic;
    UPDATE:     in std_logic;

    -- The I/O access ports
    CORE_OUT:   in std_logic_vector(IOTYPES'range);
    CORE_IN:    out std_logic_vector(IOTYPES'range);
    CORE_EN:    in std_logic_vector(IOTYPES'range);

    -- The pad connections
    PAD_OUT:    out std_logic_vector(IOTYPES'range);
    PAD_IN:     in std_logic_vector(IOTYPES'range);
    PAD_EN:     out std_logic_vector(IOTYPES'range)
  );
end c4m_jtag_ioblock;

architecture rtl of c4m_jtag_ioblock is
  signal IOMODE:        SRIOMODE_TYPE;
  signal SAMPLEMODE:    SRSAMPLEMODE_TYPE;
  signal ISSAMPLECMD:   boolean;
  
  signal BDSR_IN:       std_logic_vector(0 to IOTYPES'length-1);
  signal BDSR_OUT:      std_logic_vector(0 to IOTYPES'length-1);
  
  constant CMD_SAMPLEPRELOAD: std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_samplepreload(IR_WIDTH);
  constant CMD_EXTEST:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_extest(IR_WIDTH);
begin

  -- JTAG baundary scan IO cells
  IOGEN: for i in IOTYPES'low to IOTYPES'high generate
  begin
    IOCELL: c4m_jtag_iocell
      generic map (
        IOTYPE => IOTYPES(i)
      )
      port map (
        CORE_IN => CORE_IN(i),
        CORE_OUT => CORE_OUT(i),
        CORE_EN => CORE_EN(i),
        PAD_IN => PAD_IN(i),
        PAD_OUT => PAD_OUT(i),
        PAD_EN => PAD_EN(i),
        BDSR_IN => BDSR_IN(i-IOTYPES'low),
        BDSR_OUT => BDSR_OUT(i-IOTYPES'low),
        IOMODE => IOMODE,
        SAMPLEMODE => SAMPLEMODE,
        TCK => TCK
      );
  end generate;
  BDSRCONN: for i in 0 to BDSR_IN'length-2 generate
  begin
    BDSR_IN(i+1) <= BDSR_OUT(i);
  end generate;
  BDSR_IN(BDSR_IN'low) <= TDI;

  -- Set IOMODE
  -- Currently SR_2Pad, SR_2Core or SR_Z are not used
  -- We cheat by letting CMD_EXTEST handle both connection
  -- to pad and core.
  -- TODO: Handle more IOMODEs
  IOMODE <= SR_2PadCore when IR = CMD_EXTEST else
            SR_Through;

  -- Set SAMPLEMODE
  ISSAMPLECMD <= (IR = CMD_SAMPLEPRELOAD or IR = CMD_EXTEST);
  SAMPLEMODE <= SR_Sample when ISSAMPLECMD and CAPTURE = '1' else
                SR_Update when ISSAMPLECMD and UPDATE = '1' else
                SR_Shift when ISSAMPLECMD and SHIFT = '1' else
                SR_Normal;

  TDO <= BDSR_OUT(BDSR_IN'high) when ISSAMPLECMD and SHIFT = '1' else
         '0';
  TDO_EN <= '1' when ISSAMPLECMD and SHIFT = '1' else
            '0';
end rtl;
