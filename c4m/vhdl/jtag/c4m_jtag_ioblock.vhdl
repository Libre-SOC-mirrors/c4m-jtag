-- The block of io cells with JTAG boundary scan support

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_ioblock is
  generic (
    IR_WIDTH:   integer := 2;
    IOS:        integer := 1
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
    CORE_OUT:   in std_logic_vector(IOS-1 downto 0);
    CORE_IN:    out std_logic_vector(IOS-1 downto 0);
    CORE_EN:    in std_logic_vector(IOS-1 downto 0);

    -- The pad connections
    PAD_OUT:    out std_logic_vector(IOS-1 downto 0);
    PAD_IN:     in std_logic_vector(IOS-1 downto 0);
    PAD_EN:     out std_logic_vector(IOS-1 downto 0)
  );
end c4m_jtag_ioblock;

architecture rtl of c4m_jtag_ioblock is
  signal IOMODE:        SRIOMODE_TYPE;
  signal SAMPLEMODE:    SRSAMPLEMODE_TYPE;
  signal ISSAMPLECMD:   boolean;
  
  signal BDSR_IN:       std_logic_vector(IOS-1 downto 0);
  signal BDSR_OUT:      std_logic_vector(IOS-1 downto 0);
  
  constant CMD_SAMPLEPRELOAD: std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_samplepreload(IR_WIDTH);
  constant CMD_EXTEST:  std_logic_vector(IR_WIDTH-1 downto 0) := c4m_jtag_cmd_extest(IR_WIDTH);
begin
  -- JTAG baundary scan IO cells
  IOGEN: for i in 0 to IOS-1 generate
  begin
    IOCELL: c4m_jtag_iocell
      port map (
        CORE_IN => CORE_IN(i),
        CORE_OUT => CORE_OUT(i),
        CORE_EN => CORE_EN(i),
        PAD_IN => PAD_IN(i),
        PAD_OUT => PAD_OUT(i),
        PAD_EN => PAD_EN(i),
        BDSR_IN => BDSR_IN(i),
        BDSR_OUT => BDSR_OUT(i),
        IOMODE => IOMODE,
        SAMPLEMODE => SAMPLEMODE,
        TCK => TCK
      );
  end generate;
  BDSRCONN: for i in 0 to IOS-2 generate
  begin
    BDSR_IN(i+1) <= BDSR_OUT(i);
  end generate;
  BDSR_IN(0) <= TDI;

  -- Set IOMODE
  -- Currently SR_2Core or SR_Z are not used
  -- TODO: Handle more IOMODEs
  IOMODE <= SR_2Pad when IR = CMD_EXTEST else
            SR_Through;

  -- Set SAMPLEMODE
  ISSAMPLECMD <= (IR = CMD_SAMPLEPRELOAD or IR = CMD_EXTEST);
  SAMPLEMODE <= SR_Sample when ISSAMPLECMD and CAPTURE = '1' else
                SR_Update when ISSAMPLECMD and UPDATE = '1' else
                SR_Shift when ISSAMPLECMD and SHIFT = '1' else
                SR_Normal;

  TDO <= BDSR_OUT(IOS-1) when ISSAMPLECMD and SHIFT = '1' else
         '0';
  TDO_EN <= '1' when ISSAMPLECMD and SHIFT = '1' else
            '0';
end rtl;
