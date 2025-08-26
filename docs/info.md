<!---
This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.
You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

# QuadPWM - 4-Channel Variable Duty Cycle PWM Generator

**QuadPWM** is a sophisticated multi-channel Pulse Width Modulation generator that provides four completely independent PWM outputs with individual duty cycle control. This digital design is perfect for applications requiring precise timing control such as LED brightness management, motor speed regulation, and multi-channel analog signal generation.

## How it works

QuadPWM implements a counter-comparator architecture with advanced channel management and configurable timing to generate four independent PWM signals.

### Core Architecture

The PWM generator consists of several key components:

1. **Master PWM Counter**: A single 8-bit counter (0-255) provides the timebase for all four channels, ensuring perfect synchronization
2. **Individual Duty Cycle Registers**: Each of the four channels has its own 8-bit duty cycle storage register (0-255)
3. **Channel Comparators**: Four independent comparators generate PWM signals by comparing the master counter with individual duty cycle values
4. **Configurable Prescaler**: 8-position clock divider provides different PWM frequencies (/1, /2, /4, /8, /16, /32, /64, /128)
5. **Channel Selection Logic**: Real-time programming interface for updating duty cycles

### PWM Generation Process

Each PWM channel follows this algorithm:
- **When master_counter < channel_duty_cycle**: PWM output = HIGH (1)
- **When master_counter ≥ channel_duty_cycle**: PWM output = LOW (0)

This creates independent square waves where each channel's HIGH time is proportional to its duty cycle value.

### Channel Programming Sequence

1. **Select Channel**: Use ui_in[1:0] to choose channel (0-3)
2. **Set Duty Cycle**: Apply 8-bit value (0-255) to uio_in[7:0]
3. **Load Value**: Assert ui_in[2] (LOAD_ENABLE) to store the new duty cycle
4. **Repeat**: Program other channels as needed

### Frequency Configuration

The prescaler allows different PWM frequencies:
- **ui_in[5:3] = 000**: No division - 39.06 kHz @ 10 MHz clock
- **ui_in[5:3] = 011**: ÷8 - 4.88 kHz @ 10 MHz clock
- **ui_in[5:3] = 111**: ÷128 - 305 Hz @ 10 MHz clock

### Synchronization

All four channels share the same master counter, ensuring perfect phase alignment and synchronization. This prevents beat frequencies and provides clean, predictable multi-channel timing relationships.

## How to test

### Basic Setup

1. **Power On**: Ensure TinyTapeout demo board is powered and QuadPWM is selected
2. **Default State**: All channels initialize to 50% duty cycle (128/255)
3. **Configure Frequency**: Set prescaler using ui_in[5:3] for desired PWM frequency

### Programming Individual Channels

#### Channel 0 Programming Example
```
1. Set ui_in[1:0] = 00 (select Channel 0)
2. Set uio_in[7:0] = 64 (25% duty cycle)
3. Set ui_in = 1 (load enable HIGH)[11]
4. Set ui_in = 0 (load enable LOW)[11]
5. Observe 25% duty cycle on uo_out
```

#### Multi-Channel Programming
```
Channel 0: 25% duty → ui_in[1:0]=00, uio_in=64, toggle ui_in[11]
Channel 1: 50% duty → ui_in[1:0]=01, uio_in=128, toggle ui_in[11]
Channel 2: 75% duty → ui_in[1:0]=10, uio_in=192, toggle ui_in[11]
Channel 3: 90% duty → ui_in[1:0]=11, uio_in=230, toggle ui_in[11]
```

### Test Sequences

#### LED Brightness Test
1. Connect LEDs with 470Ω resistors to uo_out[3:0]
2. Program different duty cycles for each channel
3. Observe varying brightness levels:
   - **Duty 0**: LED OFF
   - **Duty 64**: LED dim (25% brightness)
   - **Duty 128**: LED medium (50% brightness)
   - **Duty 192**: LED bright (75% brightness)
   - **Duty 255**: LED maximum brightness

#### Oscilloscope Verification
1. Connect scope probes to uo_out[3:0]
2. Set different duty cycles per channel
3. Verify:
   - Correct duty cycle percentages
   - Synchronized timing (all channels aligned)
   - Expected PWM frequency based on prescaler setting

#### Debug Monitoring
Monitor debug outputs for system verification:
- **uo_out[4]**: Counter MSB toggles at PWM frequency/2
- **uo_out[5]**: Prescaler tick shows actual clock division
- **uo_out[6]**: Load status indicates programming activity
- **uo_out[7]**: Any-channel-active shows overall PWM activity
- **uio_out[7:0]**: Displays current duty cycle of selected channel

### Performance Verification

| Test Parameter | Expected Result | Verification Method |
|----------------|----------------|-------------------|
| Duty Cycle Accuracy | ±1% of programmed value | Oscilloscope measurement |
| Channel Independence | No crosstalk between channels | Program different values, verify isolation |
| Frequency Range | 305 Hz to 39 kHz | Measure with frequency counter |
| Synchronization | Zero phase offset | Multi-channel scope display |
| Update Speed | Immediate on load pulse | Real-time duty cycle changes |

## External hardware

### Required Components

1. **TinyTapeout Demo Board**
   - Provides 10 MHz clock, power, and I/O interface
   - Input switches/DIP switches for control
   - Standard project selection mechanism

2. **Control Interface**
   - **8-bit DIP switch bank** for duty cycle input (uio_in[7:0])
   - **3-bit switch bank** for channel selection and load control (ui_in[2:0])
   - **3-bit switch bank** for prescaler selection (ui_in[5:3])

### Demonstration Hardware

#### 4-Channel LED Display
```
Component List:
-  4x LEDs (different colors recommended)
-  4x 470Ω current-limiting resistors
-  Breadboard and connecting wires

Connections:
uo_out → 470Ω → LED1 → GND
uo_out → 470Ω → LED2 → GND[12]
uo_out → 470Ω → LED3 → GND[11]
uo_out → 470Ω → LED4 → GND[13]
```

#### Motor Speed Control Array
```
Component List:
-  4x Small DC motors (3-6V)
-  4x NPN transistors (2N2222 or similar)
-  4x 1kΩ base resistors
-  4x Flyback diodes (1N4148)

Circuit per channel:
PWM_CHx → 1kΩ → Base(NPN)
Collector(NPN) → Motor → +6V
Emitter(NPN) → GND
Flyback diode across motor
```

#### Analog Voltage Generation
```
Component List:
-  4x 1kΩ resistors
-  4x 10µF capacitors
-  Multimeter for voltage measurement

Low-pass filter per channel:
PWM_CHx → 1kΩ → Analog_Out
         ↓
        10µF
         ↓  
        GND

Output voltage = (duty_cycle/255) × 3.3V
```

### Advanced Testing Equipment

1. **4-Channel Oscilloscope**
   - Simultaneous monitoring of all PWM outputs
   - Duty cycle and frequency measurements
   - Phase relationship verification

2. **Logic Analyzer**
   - Digital timing analysis
   - Protocol debugging for control signals
   - Long-term capture for stability testing

3. **Frequency Counter**
   - Precise PWM frequency measurement
   - Prescaler verification
   - Clock accuracy validation

### Pin Connection Summary

| Function | Pin(s) | Connection |
|----------|--------|------------|
| **PWM Outputs** | uo_out[3:0] | Connect to LEDs, motors, or test equipment |
| **Channel Select** | ui_in[1:0] | 2-bit switch for channel selection (0-3) |
| **Load Enable** | ui_in[2] | Push button or toggle switch |
| **Prescaler** | ui_in[5:3] | 3-bit switch for frequency selection |
| **Duty Cycle** | uio_in[7:0] | 8-bit DIP switch bank |
| **Debug Outputs** | uo_out[7:4] | Optional scope connections |
| **Duty Readback** | uio_out[7:0] | Optional LED bank for duty display |

QuadPWM provides a comprehensive platform for learning multi-channel PWM concepts while demonstrating practical applications in motor control, LED management, and analog signal synthesis.
