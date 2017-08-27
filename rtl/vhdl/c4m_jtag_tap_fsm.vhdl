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
    STATE:      out TAPSTATE_TYPE;
    NEXT_STATE: out TAPSTATE_TYPE;
    DRSTATE:    out std_logic;
    IRSTATE:    out std_logic
  );
end c4m_jtag_tap_fsm;

architecture rtl of c4m_jtag_tap_fsm is
  signal S_STATE:         TAPSTATE_TYPE;
  signal S_NEXT_STATE:    TAPSTATE_TYPE;
  signal S_DRSTATE:       std_logic;
  signal S_IRSTATE:       std_logic;
  signal NEXT_DRSTATE:    std_logic;
  signal NEXT_IRSTATE:    std_logic;
begin
  STATE <= S_STATE;
  NEXT_STATE <= S_NEXT_STATE;
  DRSTATE <= S_DRSTATE;
  IRSTATE <= S_IRSTATE;
  
  process (TCK, TRST_N)
  begin
    if TRST_N = '0' then
      S_DRSTATE <= '0';
      S_IRSTATE <= '0';
      S_STATE <= TestLogicReset;
    elsif rising_edge(TCK) then
      S_STATE <= S_NEXT_STATE;
      S_DRSTATE <= NEXT_DRSTATE;
      S_IRSTATE <= NEXT_IRSTATE;
    end if;
  end process;

  NEXT_DRSTATE <=
    '0' when S_NEXT_STATE = TestLogicReset else
    '0' when S_NEXT_STATE = RunTestIdle else
    '1' when S_NEXT_STATE = SelectDRScan else
    '0' when S_NEXT_STATE = SelectIRScan else
    S_DRSTATE;
  NEXT_IRSTATE <=
    '0' when S_NEXT_STATE = TestLogicReset else
    '0' when S_NEXT_STATE = RunTestIdle else
    '0' when S_NEXT_STATE = SelectDRScan else
    '1' when S_NEXT_STATE = SelectIRScan else
    S_IRSTATE;

  process (S_STATE, TMS)
  begin
    case S_STATE is
      when TestLogicReset =>
        if (TMS = '0') then
          S_NEXT_STATE <= RunTestIdle;
        else
          S_NEXT_STATE <= TestLogicReset;
        end if;

      when RunTestIdle =>
        if (TMS = '0') then
          S_NEXT_STATE <= RunTestIdle;
        else
          S_NEXT_STATE <= SelectDRScan;
        end if;

      when SelectDRScan =>
        if (TMS = '0') then
          S_NEXT_STATE <= Capture;
        else
          S_NEXT_STATE <= SelectIRScan;
        end if;

      when SelectIRScan =>
        if (TMS = '0') then
          S_NEXT_STATE <= Capture;
        else
          S_NEXT_STATE <= TestLogicReset;
        end if;

      when Capture =>
        if (TMS = '0') then
          S_NEXT_STATE <= Shift;
        else
          S_NEXT_STATE <= Exit1;
        end if;

      when Shift =>
        if (TMS = '0') then
          S_NEXT_STATE <= Shift;
        else
          S_NEXT_STATE <= Exit1;
        end if;

      when Exit1 =>
        if (TMS = '0') then
          S_NEXT_STATE <= Pause;
        else
          S_NEXT_STATE <= Update;
        end if;

      when Pause =>
        if (TMS = '0') then
          S_NEXT_STATE <= Pause;
        else
          S_NEXT_STATE <= Exit2;
        end if;

      when Exit2 =>
        if (TMS = '0') then
          S_NEXT_STATE <= Shift;
        else
          S_NEXT_STATE <= Update;
        end if;

      when Update =>
        if (TMS = '0') then
          S_NEXT_STATE <= RunTestIdle;
        else
          S_NEXT_STATE <= SelectDRScan;
        end if;

      when others =>
        S_NEXT_STATE <= TestLogicReset;
    end case;
  end process;
end rtl;
