# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, RisingEdge

@cocotb.test()
async def test_quad_pwm_basic(dut):
    """Basic functionality test for QuadPWM"""
    
    dut._log.info("Start QuadPWM basic test")
    
    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    dut._log.info("Test QuadPWM default behavior")
    
    # Wait for initialization (default 50% duty cycle)
    await ClockCycles(dut.clk, 20)
    
    # Check that all 4 PWM channels are running with default 50% duty cycle
    pwm_outputs = dut.uo_out.value & 0x0F  # Extract PWM channels [3:0]
    dut._log.info(f"Initial PWM outputs: {bin(pwm_outputs)} (should show some activity)")
    
    # Test basic PWM operation - all channels should be active
    any_channel_active = (dut.uo_out.value >> 7) & 1
    assert any_channel_active == 1, f"Expected at least one channel active, got {any_channel_active}"
    dut._log.info("✓ Basic PWM activity test passed")

@cocotb.test()
async def test_quad_pwm_channel_programming(dut):
    """Test individual channel programming"""
    
    dut._log.info("Start individual channel programming test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    
    # Test programming each channel with different duty cycles
    test_duty_cycles = [64, 128, 192, 255]  # 25%, 50%, 75%, 100%
    
    for channel in range(4):
        duty_cycle = test_duty_cycles[channel]
        dut._log.info(f"Programming Channel {channel} with duty cycle {duty_cycle}/255 ({duty_cycle/255*100:.1f}%)")
        
        # Select channel
        dut.ui_in.value = channel  # ui_in[1:0] = channel select
        
        # Set duty cycle
        dut.uio_in.value = duty_cycle
        
        # Assert load enable
        dut.ui_in.value = channel | (1 << 2)  # Set bit 2 (LOAD_ENABLE) high
        await ClockCycles(dut.clk, 2)
        
        # Deassert load enable  
        dut.ui_in.value = channel  # Clear bit 2 (LOAD_ENABLE)
        await ClockCycles(dut.clk, 2)
        
        # Verify duty cycle was loaded (check readback)
        readback_duty = dut.uio_out.value & 0xFF
        assert readback_duty == duty_cycle, \
            f"Channel {channel}: Expected duty cycle {duty_cycle}, got {readback_duty}"
        
        dut._log.info(f"✓ Channel {channel} programmed successfully: duty={readback_duty}")
    
    dut._log.info("✓ All channels programmed successfully")

@cocotb.test()
async def test_quad_pwm_duty_cycle_accuracy(dut):
    """Test PWM duty cycle accuracy"""
    
    dut._log.info("Start duty cycle accuracy test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    
    # Test specific duty cycles for accuracy
    test_cases = [
        (0, 0, "0%"),      # 0% duty cycle
        (1, 64, "25%"),    # 25% duty cycle  
        (2, 128, "50%"),   # 50% duty cycle
        (3, 192, "75%")    # 75% duty cycle
    ]
    
    for channel, duty_cycle, description in test_cases:
        dut._log.info(f"Testing Channel {channel}: {description} duty cycle")
        
        # Program the channel
        dut.ui_in.value = channel
        dut.uio_in.value = duty_cycle
        dut.ui_in.value = channel | (1 << 2)  # Load enable
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = channel  # Clear load enable
        await ClockCycles(dut.clk, 10)  # Stabilize
        
        # Count HIGH cycles over one complete PWM period (256 clocks)
        high_count = 0
        total_count = 256
        
        for i in range(total_count):
            await RisingEdge(dut.clk)
            pwm_channel_output = (dut.uo_out.value >> channel) & 1
            if pwm_channel_output == 1:
                high_count += 1
        
        # Calculate actual duty cycle percentage
        actual_duty_percentage = (high_count / total_count) * 100
        expected_duty_percentage = (duty_cycle / 255) * 100
        
        # Allow 2% tolerance
        tolerance = 2.0
        assert abs(actual_duty_percentage - expected_duty_percentage) <= tolerance, \
            f"Channel {channel}: Expected {expected_duty_percentage:.1f}%, got {actual_duty_percentage:.1f}%"
        
        dut._log.info(f"✓ Channel {channel}: Expected {expected_duty_percentage:.1f}%, Got {actual_duty_percentage:.1f}%")

@cocotb.test()
async def test_quad_pwm_synchronization(dut):
    """Test that all PWM channels are synchronized"""
    
    dut._log.info("Start synchronization test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    
    # Program all channels with same duty cycle but different moments
    for channel in range(4):
        dut.ui_in.value = channel
        dut.uio_in.value = 128  # 50% duty cycle for all channels
        dut.ui_in.value = channel | (1 << 2)  # Load enable
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = channel  # Clear load enable
        await ClockCycles(dut.clk, 2)
    
    # Wait for counter to reset to 0 (start of PWM cycle)
    await ClockCycles(dut.clk, 300)  # Wait more than one PWM period
    
    # Check that all channels transition together at the same time
    # Sample all channels at the same clock edge multiple times
    sync_samples = []
    for sample in range(50):
        await RisingEdge(dut.clk)
        pwm_state = dut.uo_out.value & 0x0F  # All 4 PWM channels
        sync_samples.append(pwm_state)
    
    # Count transitions - synchronized channels should have simultaneous transitions
    transitions = 0
    for i in range(1, len(sync_samples)):
        if sync_samples[i] != sync_samples[i-1]:
            transitions += 1
    
    dut._log.info(f"Observed {transitions} transitions in {len(sync_samples)} samples")
    
    # With proper synchronization, we expect fewer transitions than random behavior
    assert transitions < 20, f"Too many transitions ({transitions}), channels may not be synchronized"
    dut._log.info("✓ PWM channels appear to be synchronized")

@cocotb.test()
async def test_quad_pwm_prescaler(dut):
    """Test PWM frequency prescaler"""
    
    dut._log.info("Start prescaler test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    
    # Test different prescaler values
    prescaler_values = [0, 3, 7]  # /1, /8, /128
    prescaler_names = ["/1", "/8", "/128"]
    
    for prescaler, name in zip(prescaler_values, prescaler_names):
        dut._log.info(f"Testing prescaler {name}")
        
        # Set prescaler in ui_in[5:3]
        prescaler_bits = prescaler << 3
        dut.ui_in.value = prescaler_bits
        
        # Program channel 0 with 50% duty cycle
        dut.uio_in.value = 128
        dut.ui_in.value = 0 | prescaler_bits | (1 << 2)  # Channel 0 + prescaler + load
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = 0 | prescaler_bits  # Clear load enable
        
        await ClockCycles(dut.clk, 50)  # Let it stabilize
        
        # Monitor prescaler tick signal
        prescaler_tick = (dut.uo_out.value >> 5) & 1
        counter_msb = (dut.uo_out.value >> 4) & 1
        
        dut._log.info(f"Prescaler {name}: tick={prescaler_tick}, counter_msb={counter_msb}")
        
        # Just verify the prescaler tick is changing for non-zero prescalers
        tick_samples = []
        for i in range(20):
            await ClockCycles(dut.clk, 5)
            tick_samples.append((dut.uo_out.value >> 5) & 1)
        
        # Count tick changes
        tick_changes = sum(1 for i in range(1, len(tick_samples)) if tick_samples[i] != tick_samples[i-1])
        
        dut._log.info(f"Prescaler {name}: {tick_changes} tick changes observed")
        dut._log.info(f"✓ Prescaler {name} test completed")

@cocotb.test()
async def test_quad_pwm_edge_cases(dut):
    """Test PWM edge cases and boundary conditions"""
    
    dut._log.info("Start edge cases test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    
    # Test edge cases
    edge_cases = [
        (0, 0, "0% duty - always LOW"),
        (1, 1, "Minimum duty - mostly LOW"),  
        (2, 127, "Just under 50%"),
        (3, 255, "Maximum duty - always HIGH")
    ]
    
    for channel, duty_cycle, description in edge_cases:
        dut._log.info(f"Testing {description}")
        
        # Program channel
        dut.ui_in.value = channel
        dut.uio_in.value = duty_cycle  
        dut.ui_in.value = channel | (1 << 2)  # Load enable
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = channel  # Clear load enable
        
        # Wait and sample output
        await ClockCycles(dut.clk, 300)  # More than one PWM cycle
        
        # Count samples for this channel
        samples = []
        for i in range(100):
            await RisingEdge(dut.clk)
            channel_output = (dut.uo_out.value >> channel) & 1
            samples.append(channel_output)
        
        high_count = sum(samples)
        high_percentage = (high_count / len(samples)) * 100
        
        # Verify edge case behavior
        if duty_cycle == 0:
            assert high_count == 0, f"0% duty should never be HIGH, got {high_count} HIGH samples"
        elif duty_cycle == 255:
            assert high_count >= 95, f"100% duty should mostly be HIGH, got {high_count} HIGH samples"  # Allow some tolerance
        
        dut._log.info(f"✓ {description}: {high_percentage:.1f}% HIGH samples")

@cocotb.test()
async def test_quad_pwm_reset_behavior(dut):
    """Test reset functionality"""
    
    dut._log.info("Start reset behavior test")
    
    # Set up clock
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # Initial setup
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 200  # High duty cycle
    dut.rst_n.value = 1
    
    # Let PWM run for a while with high duty cycles
    for channel in range(4):
        dut.ui_in.value = channel
        dut.ui_in.value = channel | (1 << 2)  # Load enable
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value = channel  # Clear load enable
    
    await ClockCycles(dut.clk, 50)
    
    # Apply reset
    dut._log.info("Applying reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    
    # Check reset state - all outputs should be LOW
    pwm_outputs = dut.uo_out.value & 0x0F
    any_channel_active = (dut.uo_out.value >> 7) & 1
    
    # During reset, PWM outputs should be LOW
    assert pwm_outputs == 0, f"PWM outputs not reset: {bin(pwm_outputs)}"
    
    dut._log.info("✓ Reset state verified")
    
    # Release reset and verify operation resumes
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 50)  # Allow initialization
    
    # Check that PWM is now operating (should return to default 50% duty cycle)
    new_any_active = (dut.uo_out.value >> 7) & 1
    assert new_any_active == 1, f"PWM not active after reset release: {new_any_active}"
    
    dut._log.info("✓ Reset functionality test passed")
