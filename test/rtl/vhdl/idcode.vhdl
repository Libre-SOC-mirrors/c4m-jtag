-- reset JTAG interface and then IDCODE should be shifted out

library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity bench_idcode is
end bench_idcode;

architecture rtl of bench_idcode is
  signal TCK:   std_logic;
  signal TMS:   std_logic;
  signal TDI:   std_logic;
  signal TDO:   std_logic;
  signal TRST_N: std_logic;

  constant CLK_PERIOD:  time := 10 ns;

  procedure ClkCycle(
    signal CLK: out std_logic;
    CLK_PERIOD: time
  ) is
  begin
    CLK <= '0';
    wait for CLK_PERIOD/4;
    CLK <= '1';
    wait for CLK_PERIOD/2;
    CLK <= '0';
    wait for CLK_PERIOD/4;
  end ClkCycle;

  procedure ClkCycles(
    N:  integer;
    signal CLK: out std_logic;
    CLK_PERIOD: time
  ) is
  begin
    for i in 1 to N loop
      ClkCycle(CLK, CLK_PERIOD);
    end loop;
  end ClkCycles;
begin
  JTAG_BLOCK: c4m_jtag_tap_controller
    -- Use default values
    port map (
      TCK => TCK,
      TMS => TMS,
      TDI => TDI,
      TDO => TDO,
      TRST_N => TRST_N,
      RESET => open,
      DRCAPTURE => open,
      DRSHIFT => open,
      DRUPDATE => open,
      IR => open,
      CORE_OUT => "0",
      CORE_IN => open,
      CORE_EN => "0",
      PAD_OUT => open,
      PAD_IN => "0",
      PAD_EN => open
    );

  SIM: process
  begin
    -- Reset
    TCK <= '0';
    TMS <= '1';
    TDI <= '0';
    TRST_N <= '0';
    wait for 10*CLK_PERIOD;

    TRST_N <= '1';
    wait for CLK_PERIOD;

    -- Enter RunTestIdle
    TMS <= '0';
    ClkCycle(TCK, CLK_PERIOD);
    -- Enter SelectDRScan
    TMS <= '1';
    ClkCycle(TCK, CLK_PERIOD);
    -- Enter Capture
    TMS <= '0';
    ClkCycle(TCK, CLK_PERIOD);
    -- Enter Shift, run for 35 CLK cycles
    TMS <= '0';
    ClkCycles(35, TCK, CLK_PERIOD);
    -- Enter Exit1
    TMS <= '1';
    ClkCycle(TCK, CLK_PERIOD);
    -- Enter Update
    TMS <= '1';
    ClkCycle(TCK, CLK_PERIOD);
    -- To TestLogicReset
    TMS <= '1';
    ClkCycles(4, TCK, CLK_PERIOD);

    -- end simulation
    wait;
  end process;
end rtl;
