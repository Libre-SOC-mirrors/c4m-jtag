-- Package of jtag support code from the Chips4Makers project
library ieee;
use ieee.std_logic_1164.ALL;

package c4m_jtag is
  type TAPSTATE_TYPE is (
    TestLogicReset,
    RunTestIdle,
    SelectDRScan,
    SelectIRScan,
    Capture,
    Shift,
    Exit1,
    Pause,
    Exit2,
    Update
  );
  type SRIOMODE_TYPE is (
    SR_Through, -- Connect core signal to pad signals
    SR_2Pad,    -- Connect BD to pad
    SR_2Core,   -- Connect BD to core
    SR_Z        -- pad is high impedance
  );
  type SRSAMPLEMODE_TYPE is (
    SR_Normal,  -- No sampling or shifting
    SR_Sample,  -- Sample IO state in BD SR on rising edge of TCK
    SR_Update,  -- Update BD from SR on falling edge of TCK
    SR_Shift    -- Shift the BD SR
  );

  function c4m_jtag_cmd_idcode(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_bypass(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_samplepreload(width: integer) return std_logic_vector;
  function c4m_jtag_cmd_extest(width: integer) return std_logic_vector;

  component c4m_jtag_tap_fsm is
    port (
      -- The TAP signals
      TCK:      in std_logic;
      TMS:      in std_logic;
      TRST_N:   in std_logic;

      -- The state outputs
      STATE:    out TAPSTATE_TYPE;
      NEXT_STATE: out TAPSTATE_TYPE;
      DRSTATE:  out std_logic;
      IRSTATE:  out std_logic
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
    
      -- JTAG state
      STATE:    in TAPSTATE_TYPE;
      NEXT_STATE: in TAPSTATE_TYPE;
      IRSTATE:  in std_logic;

      -- instruction register
      IR:       out std_logic_vector(IR_WIDTH-1 downto 0)
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

      -- JTAG state
      STATE:    in TAPSTATE_TYPE;
      NEXT_STATE: in TAPSTATE_TYPE;
      DRSTATE:  in std_logic;

      -- The instruction
      IR:       in std_logic_vector(IR_WIDTH-1 downto 0)
    );
  end component c4m_jtag_idblock;

  component c4m_jtag_iocell is
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
      IOS:      integer := 1
    );
    port (
      -- needed TAP signals
      TCK:      in std_logic;
      TDI:      in std_logic;
      TDO:      out std_logic;
      TDO_EN:   out std_logic;

      -- JTAG state
      STATE:    in TAPSTATE_TYPE;
      NEXT_STATE: in TAPSTATE_TYPE;
      DRSTATE:  in std_logic;

      -- The instruction
      IR:       in std_logic_vector(IR_WIDTH-1 downto 0);

      -- The I/O access ports
      CORE_OUT: in std_logic_vector(IOS-1 downto 0);
      CORE_IN:  out std_logic_vector(IOS-1 downto 0);
      CORE_EN:  in std_logic_vector(IOS-1 downto 0);

      -- The pad connections
      PAD_OUT:  out std_logic_vector(IOS-1 downto 0);
      PAD_IN:   in std_logic_vector(IOS-1 downto 0);
      PAD_EN:   out std_logic_vector(IOS-1 downto 0)
    );
  end component c4m_jtag_ioblock;

  component c4m_jtag_tap_controller is
    generic (
      DEBUG:            boolean := false;

      IR_WIDTH:         integer := 2;
      IOS:              integer := 1;

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

      -- The FSM state indicators
      RESET:    out std_logic; -- In reset state
      DRCAPTURE: out std_logic; -- In DR_Capture state
      DRSHIFT:  out std_logic; -- In DR_Shift state
      DRUPDATE: out std_logic; -- In DR_Update state

      -- The Instruction Register
      IR:       out std_logic_vector(IR_WIDTH-1 downto 0);

      -- The I/O access ports
      CORE_IN:  out std_logic_vector(IOS-1 downto 0);
      CORE_EN:  in std_logic_vector(IOS-1 downto 0);
      CORE_OUT: in std_logic_vector(IOS-1 downto 0);

      -- The pad connections
      PAD_IN:   in std_logic_vector(IOS-1 downto 0);
      PAD_EN:   out std_logic_vector(IOS-1 downto 0);
      PAD_OUT:  out std_logic_vector(IOS-1 downto 0)
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
end package body;
