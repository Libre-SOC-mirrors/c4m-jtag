-- The JTAG state machine
-- This is implemented based on the IEEE 1149.1 standard

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity c4m_jtag_tap_fsm is
  port (
    -- The TAP signals
    TCK:        in std_logic;
    TMS:        in std_logic;
    TRST_N:     in std_logic;

    -- The state outputs
    RESET:      out std_logic;
    ISDR:       out std_logic;
    ISIR:       out std_logic;
    CAPTURE:    out std_logic;
    SHIFT:      out std_logic;
    UPDATE:     out std_logic
  );
end c4m_jtag_tap_fsm;

architecture rtl of c4m_jtag_tap_fsm is
  type TAPSTATE_TYPE is (
    TestLogicReset,
    RunTestIdle,
    SelectDRScan,
    SelectIRScan,
    CaptureState,
    ShiftState,
    Exit1,
    Pause,
    Exit2,
    UpdateState
  );
  signal STATE:         TAPSTATE_TYPE;
  signal DRSTATE:       std_logic;
  signal IRSTATE:       std_logic;
  signal NEXT_STATE:    TAPSTATE_TYPE;
  signal NEXT_DRSTATE:  std_logic;
  signal NEXT_IRSTATE:  std_logic;
begin
  -- Generate outputs from the state
  ISDR    <= DRSTATE;
  ISIR    <= IRSTATE;
  RESET   <= '1' when STATE = TestLogicReset else '0';
  CAPTURE <= '1' when STATE = CaptureState   else '0';
  SHIFT   <= '1' when STATE = ShiftState     else '0';
  UPDATE  <= '1' when STATE = UpdateState    else '0';

  process (TCK, TRST_N)
  begin
    if TRST_N = '0' then
      DRSTATE <= '0';
      IRSTATE <= '0';
      STATE <= TestLogicReset;
    elsif rising_edge(TCK) then
      STATE <= NEXT_STATE;
      DRSTATE <= NEXT_DRSTATE;
      IRSTATE <= NEXT_IRSTATE;
    end if;
  end process;

  NEXT_DRSTATE <=
    '0' when NEXT_STATE = TestLogicReset else
    '0' when NEXT_STATE = RunTestIdle else
    '1' when NEXT_STATE = SelectDRScan else
    '0' when NEXT_STATE = SelectIRScan else
    DRSTATE;
  NEXT_IRSTATE <=
    '0' when NEXT_STATE = TestLogicReset else
    '0' when NEXT_STATE = RunTestIdle else
    '0' when NEXT_STATE = SelectDRScan else
    '1' when NEXT_STATE = SelectIRScan else
    IRSTATE;

  process (STATE, TMS)
  begin
    case STATE is
      when TestLogicReset =>
        if (TMS = '0') then
          NEXT_STATE <= RunTestIdle;
        else
          NEXT_STATE <= TestLogicReset;
        end if;

      when RunTestIdle =>
        if (TMS = '0') then
          NEXT_STATE <= RunTestIdle;
        else
          NEXT_STATE <= SelectDRScan;
        end if;

      when SelectDRScan =>
        if (TMS = '0') then
          NEXT_STATE <= CaptureState;
        else
          NEXT_STATE <= SelectIRScan;
        end if;

      when SelectIRScan =>
        if (TMS = '0') then
          NEXT_STATE <= CaptureState;
        else
          NEXT_STATE <= TestLogicReset;
        end if;

      when CaptureState =>
        if (TMS = '0') then
          NEXT_STATE <= ShiftState;
        else
          NEXT_STATE <= Exit1;
        end if;

      when ShiftState =>
        if (TMS = '0') then
          NEXT_STATE <= ShiftState;
        else
          NEXT_STATE <= Exit1;
        end if;

      when Exit1 =>
        if (TMS = '0') then
          NEXT_STATE <= Pause;
        else
          NEXT_STATE <= UpdateState;
        end if;

      when Pause =>
        if (TMS = '0') then
          NEXT_STATE <= Pause;
        else
          NEXT_STATE <= Exit2;
        end if;

      when Exit2 =>
        if (TMS = '0') then
          NEXT_STATE <= ShiftState;
        else
          NEXT_STATE <= UpdateState;
        end if;

      when UpdateState =>
        if (TMS = '0') then
          NEXT_STATE <= RunTestIdle;
        else
          NEXT_STATE <= SelectDRScan;
        end if;

      when others =>
        NEXT_STATE <= TestLogicReset;
    end case;
  end process;
end rtl;
