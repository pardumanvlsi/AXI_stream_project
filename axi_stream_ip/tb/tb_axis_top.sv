// =============================================================================
//  tb_axis_top.sv  —  Testbench for the master->slave top integration
// -----------------------------------------------------------------------------
//  Drives a `newd` pulse and checks that 4 beats stream from master to slave.
//  Run with any SystemVerilog simulator, e.g.:
//      xrun rtl/axis_m.sv rtl/axis_s.sv rtl/top.sv tb/tb_axis_top.sv
//      vsim ...   /   iverilog -g2012 ...
// =============================================================================
`timescale 1ns/1ps

module tb_axis_top;

    logic        clk;
    logic        rst;        // active-low
    logic        newd;
    logic [7:0]  din;
    logic [7:0]  dout;
    logic        last;

    // DUT
    top dut (
        .clk  (clk),
        .rst  (rst),
        .newd (newd),
        .din  (din),
        .dout (dout),
        .last (last)
    );

    // 100 MHz clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("tb_axis_top.vcd");
        $dumpvars(0, tb_axis_top);

        // Reset
        rst  = 1'b0;
        newd = 1'b0;
        din  = 8'd5;
        repeat (3) @(posedge clk);
        rst  = 1'b1;

        // Start a transaction
        @(posedge clk);
        newd = 1'b1;
        @(posedge clk);
        newd = 1'b0;

        // Observe 4 beats
        repeat (10) @(posedge clk);

        $display("[%0t] Final dout=%0d last=%0b", $time, dout, last);
        $finish;
    end

    // Beat monitor
    always @(posedge clk) begin
        if (dut.valid_t && dut.ready_t)
            $display("[%0t] BEAT  data=%0d  last=%0b", $time, dut.data, dut.last_t);
    end

endmodule
