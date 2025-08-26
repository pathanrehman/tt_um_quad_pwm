/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_quad_pwm (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // Input Configuration
    wire [1:0] channel_select = ui_in[1:0];     // Channel selector (0-3)
    wire [7:0] duty_cycle_input = uio_in[7:0];  // 8-bit duty cycle input
    wire load_enable = ui_in[2];               // Load new duty cycle when high
    wire [2:0] prescaler_select = ui_in[5:3];  // Clock prescaler selection

    // Internal Signals
    reg [7:0] pwm_counter;           // Main PWM counter (0-255)
    reg [7:0] duty_cycle [0:3];      // Duty cycle storage for 4 channels
    reg [3:0] pwm_outputs;           // PWM outputs for 4 channels
    reg [7:0] prescaler_counter;     // Clock prescaler counter
    wire prescaler_tick;             // Prescaler output tick
    
    // Clock Prescaler - generates different PWM frequencies
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prescaler_counter <= 8'b0;
        end else if (ena) begin
            case (prescaler_select)
                3'b000: prescaler_counter <= prescaler_counter + 1;      // /1 - Full speed
                3'b001: prescaler_counter <= prescaler_counter + 1;      // /2
                3'b010: prescaler_counter <= prescaler_counter + 1;      // /4
                3'b011: prescaler_counter <= prescaler_counter + 1;      // /8
                3'b100: prescaler_counter <= prescaler_counter + 1;      // /16
                3'b101: prescaler_counter <= prescaler_counter + 1;      // /32
                3'b110: prescaler_counter <= prescaler_counter + 1;      // /64
                3'b111: prescaler_counter <= prescaler_counter + 1;      // /128
                default: prescaler_counter <= prescaler_counter + 1;
            endcase
        end
    end
    
    // Generate prescaler tick based on selection
    assign prescaler_tick = (prescaler_select == 3'b000) ? 1'b1 :             // /1
                           (prescaler_select == 3'b001) ? prescaler_counter[0] : // /2
                           (prescaler_select == 3'b010) ? prescaler_counter[1] : // /4
                           (prescaler_select == 3'b011) ? prescaler_counter[2] : // /8
                           (prescaler_select == 3'b100) ? prescaler_counter[3] : // /16
                           (prescaler_select == 3'b101) ? prescaler_counter[4] : // /32
                           (prescaler_select == 3'b110) ? prescaler_counter[5] : // /64
                           prescaler_counter[6];                                  // /128
    
    // PWM Counter - counts from 0 to 255 for PWM generation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_counter <= 8'b0;
        end else if (ena && prescaler_tick) begin
            pwm_counter <= pwm_counter + 1;  // Auto-increments and rolls over at 256
        end
    end
    
    // Duty Cycle Register Update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Initialize all channels to 50% duty cycle
            duty_cycle[0] <= 8'd128;
            duty_cycle[1] <= 8'd128;
            duty_cycle[2] <= 8'd128;
            duty_cycle[3] <= 8'd128;
        end else if (ena && load_enable) begin
            // Load new duty cycle for selected channel
            case (channel_select)
                2'b00: duty_cycle[0] <= duty_cycle_input;
                2'b01: duty_cycle[1] <= duty_cycle_input;
                2'b10: duty_cycle[2] <= duty_cycle_input;
                2'b11: duty_cycle[3] <= duty_cycle_input;
            endcase
        end
    end
    
    // PWM Generation Logic for all 4 channels
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_outputs <= 4'b0000;
        end else if (ena) begin
            // Channel 0 PWM
            if (pwm_counter < duty_cycle[0])
                pwm_outputs[0] <= 1'b1;
            else
                pwm_outputs[0] <= 1'b0;
                
            // Channel 1 PWM  
            if (pwm_counter < duty_cycle[1])
                pwm_outputs[1] <= 1'b1;
            else
                pwm_outputs[1] <= 1'b0;
                
            // Channel 2 PWM
            if (pwm_counter < duty_cycle[2])
                pwm_outputs[2] <= 1'b1;
            else
                pwm_outputs[2] <= 1'b0;
                
            // Channel 3 PWM
            if (pwm_counter < duty_cycle[3])
                pwm_outputs[3] <= 1'b1;
            else
                pwm_outputs[3] <= 1'b0;
        end
    end
    
    // Output Assignments
    assign uo_out[0] = pwm_outputs[0];      // PWM Channel 0 output
    assign uo_out[1] = pwm_outputs[1];      // PWM Channel 1 output  
    assign uo_out[2] = pwm_outputs[2];      // PWM Channel 2 output
    assign uo_out[3] = pwm_outputs[3];      // PWM Channel 3 output
    assign uo_out[4] = pwm_counter[7];      // Counter MSB (for frequency monitoring)
    assign uo_out[5] = prescaler_tick;      // Prescaler tick (for debug)
    assign uo_out[6] = load_enable;         // Load enable status (for debug)
    assign uo_out[7] = |pwm_outputs;        // Any channel active indicator
    
    // Bidirectional pins configured as outputs for extended functionality
    assign uio_out[0] = duty_cycle[channel_select][0];  // Current duty cycle LSB
    assign uio_out[1] = duty_cycle[channel_select][1];  // Current duty cycle bit 1
    assign uio_out[2] = duty_cycle[channel_select][2];  // Current duty cycle bit 2
    assign uio_out[3] = duty_cycle[channel_select][3];  // Current duty cycle bit 3
    assign uio_out[4] = duty_cycle[channel_select][4];  // Current duty cycle bit 4
    assign uio_out[5] = duty_cycle[channel_select][5];  // Current duty cycle bit 5
    assign uio_out[6] = duty_cycle[channel_select][6];  // Current duty cycle bit 6
    assign uio_out[7] = duty_cycle[channel_select][7];  // Current duty cycle MSB
    
    assign uio_oe = 8'hFF;  // All bidirectional pins configured as outputs
    
    // Unused inputs (to prevent warnings)
    wire _unused = &{ui_in[7:6], 1'b0};

endmodule
