-- Package of jtag support code from the Chips4Makers project
library ieee;
use ieee.std_logic_1164.ALL;

package c4m_jtag is
  type SRIOMODE_TYPE is (
    SR_Through, -- Connect core signal to pad signals
    SR_2Pad,    -- Connect BD to pad
    SR_2Core,   -- Connect BD to core
    SR_2PadCore, -- Connect BD to pad and core
    SR_Z        -- pad is high impedance
  );
  type SRSAMPLEMODE_TYPE is (
    SR_Normal,  -- No sampling or shifting
    SR_Sample,  -- Sample IO state in BD SR on rising edge of TCK
    SR_Update,  -- Update BD from SR on falling edge of TCK
    SR_Shift    -- Shift the BD SR
  );
  type IOTYPE_TYPE is (
    IO_IN,      -- Input only
    IO_OUT,     -- Output only, without tristate
    IO_OUT3,    -- Output only, with tristate
    IO_INOUT3   -- Input and output with tristate
  );
  type IOTYPE_VECTOR is array ( natural range <> ) of IOTYPE_TYPE;

  constant IOTYPES_NULL: IOTYPE_VECTOR(1 to 0) := (others => IO_INOUT3);

  function c4m_jtag_cmd_idcode(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_bypass(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_samplepreload(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_extest(width: integer) return std_logic_vector;
  function gen_iotypes(count: integer; iotype: IOTYPE_TYPE := IO_INOUT3) return IOTYPE_VECTOR;

  component c4m_jtag_tap_fsm is
    port (
      -- The TAP signals
      TCK:      in std_logic;
      TMS:      in std_logic;
      TRST_N:   in std_logic;

      -- The state outputs
      RESET:    out std_logic;
      ISDR:     out std_logic;
      ISIR:     out std_logic;
      CAPTURE:  out std_logic;
      SHIFT:    out std_logic;
      UPDATE:   out std_logic
    );
  end component c4m_jtag_tap_fsm;

  component c4m_jtag_irblock is
    generic (
      IR_WIDTH: integer := 2
    );
    port (
      -- needed TAP signals
      TCK:      in std_logic;
      TDI:      in std_logic;
      TDO:      out std_logic;
      TDO_EN:   out std_logic;

      -- instruction register
      IR:       out std_logic_vector(IR_WIDTH-1 downto 0);

      -- actions
      RESET:    in std_logic;
      CAPTURE:  in std_logic;
      SHIFT:    in std_logic;
      UPDATE:   in std_logic
    );
  end component c4m_jtag_irblock;
  
  component c4m_jtag_idblock is
    generic (
      IR_WIDTH:         integer := 2;
    
      -- The default MANUFACTURING ID is not representing a valid
      -- manufacturer according to the JTAG standard
      MANUFACTURER:     std_logic_vector(10 downto 0) := "10001111111";
      PART_NUMBER:      std_logic_vector(15 downto 0) := "0000000000000001";
      VERSION:          std_logic_vector(3 downto 0) := "0000"
    );
    port (
      -- needed TAP signals
      TCK:      in std_logic;
      TDI:      in std_logic;
      TDO:      out std_logic;
      TDO_EN:   out std_logic;

      -- The instruction
      IR:       in std_logic_vector(IR_WIDTH-1 downto 0);

      -- actions
      CAPTURE:  in std_logic;
      SHIFT:    in std_logic;
      UPDATE:   in std_logic
    );
  end component c4m_jtag_idblock;

  component c4m_jtag_iocell is
    generic (
      IOTYPE:   IOTYPE_TYPE
    );
    port (
      -- core connections
      CORE_IN:  out std_logic;
      CORE_OUT: in std_logic;
      CORE_EN:  in std_logic;

      -- pad connections
      PAD_IN:   in std_logic;
      PAD_OUT:  out std_logic;
      PAD_EN:   out std_logic;

      -- BD shift register
      BDSR_IN:  in std_logic;
      BDSR_OUT: out std_logic;

      -- Mode of I/O cell
      IOMODE:   in SRIOMODE_TYPE;
      SAMPLEMODE: in SRSAMPLEMODE_TYPE;
      TCK:      in std_logic
    );
  end component c4m_jtag_iocell;
  
  component c4m_jtag_ioblock is
    generic (
      IR_WIDTH: integer := 2;
      IOTYPES:  IOTYPE_VECTOR
    );
    port (
      -- needed TAP signals
      TCK:      in std_logic;
      TDI:      in std_logic;
      TDO:      out std_logic;
      TDO_EN:   out std_logic;

      -- The instruction
      IR:       in std_logic_vector(IR_WIDTH-1 downto 0);

      -- actions
      CAPTURE:  in std_logic;
      SHIFT:    in std_logic;
      UPDATE:   in std_logic;

      -- The I/O access ports
      CORE_OUT: in std_logic_vector(IOTYPES'range);
      CORE_IN:  out std_logic_vector(IOTYPES'range);
      CORE_EN:  in std_logic_vector(IOTYPES'range);

      -- The pad connections
      PAD_OUT:  out std_logic_vector(IOTYPES'range);
      PAD_IN:   in std_logic_vector(IOTYPES'range);
      PAD_EN:   out std_logic_vector(IOTYPES'range)
    );
  end component c4m_jtag_ioblock;

  component c4m_jtag_tap_controller is
    generic (
      DEBUG:            boolean := false;

      IR_WIDTH:         integer := 2;
      IOTYPES:          IOTYPE_VECTOR := IOTYPES_NULL;

      -- The default MANUFACTURING ID is not representing a valid
      -- manufacturer according to the JTAG standard
      MANUFACTURER:     std_logic_vector(10 downto 0) := "10001111111";
      PART_NUMBER:      std_logic_vector(15 downto 0) := "0000000000000001";
      VERSION:          std_logic_vector(3 downto 0) := "0000"
    );
    port (
      -- The TAP signals
      TCK:      in std_logic;
      TMS:      in std_logic;
      TDI:      in std_logic;
      TDO:      out std_logic;
      TRST_N:   in std_logic;

      -- The Instruction Register
      IR:       out std_logic_vector(IR_WIDTH-1 downto 0);

      -- The FSM state indicators
      RESET:    out std_logic; -- In reset state
      CAPTURE:  out std_logic; -- In DR_Capture state
      SHIFT:    out std_logic; -- In DR_Shift state
      UPDATE:   out std_logic; -- In DR_Update state

      -- The I/O access ports
      CORE_IN:  out std_logic_vector(IOTYPES'range);
      CORE_EN:  in std_logic_vector(IOTYPES'range);
      CORE_OUT: in std_logic_vector(IOTYPES'range);

      -- The pad connections
      PAD_IN:   in std_logic_vector(IOTYPES'range);
      PAD_EN:   out std_logic_vector(IOTYPES'range);
      PAD_OUT:  out std_logic_vector(IOTYPES'range)
    );
  end component c4m_jtag_tap_controller;
end c4m_jtag;

package body c4m_jtag is
  function c4m_jtag_cmd_bypass(width: integer) return std_logic_vector is
    variable return_vector: std_logic_vector(width-1 downto 0);
  begin
    return_vector := (others => '1');
    return return_vector;
  end;

  function c4m_jtag_cmd_idcode(width: integer) return std_logic_vector is
    variable return_vector: std_logic_vector(width-1 downto 0);
  begin
    return_vector := (0 => '1', others => '0');
    return return_vector;
  end;

  function c4m_jtag_cmd_samplepreload(width: integer) return std_logic_vector is
    variable return_vector: std_logic_vector(width-1 downto 0);
  begin
    return_vector := (1 => '1', others => '0');
    return return_vector;
  end;

  function c4m_jtag_cmd_extest(width: integer) return std_logic_vector is
    variable return_vector: std_logic_vector(width-1 downto 0);
  begin
    return_vector := (others => '0');
    return return_vector;
  end;

  function gen_iotypes(count: integer; iotype: IOTYPE_TYPE := IO_INOUT3) return IOTYPE_VECTOR is
    variable return_vector: IOTYPE_VECTOR(0 to count-1);
  begin
    return_vector := (others => iotype);
    return return_vector;
  end function gen_iotypes;
end package body;
