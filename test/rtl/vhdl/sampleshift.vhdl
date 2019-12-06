-- Test JTAG in the following way:
--  * reset JTAG interface
--  * load samplepreload command
--  * shift in/out sampled inputs + wanted outputs
--  * load extest command
--  * execute


library ieee;
use ieee.std_logic_1164.ALL;

use work.c4m_jtag.ALL;

entity bench_sampleshift is
end bench_sampleshift;

architecture rtl of bench_sampleshift is
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
  
  procedure LoadIR(
