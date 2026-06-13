// =============================================================================
//  top.sv  —  AXI4-Stream Top Integration
// -----------------------------------------------------------------------------
//  Wires the streaming master (axis_m) directly to the streaming slave (axis_s).
//  The master streams 4 beats per `newd` pulse; the slave exposes received
//  bytes on `dout`. `last` is tapped from the master's TLAST.
// =============================================================================
module top (
    input  wire       clk,
    input  wire       rst,      // active-low reset (aresetn)
    input  wire       newd,
    input  wire [7:0] din,
    output wire [7:0] dout,
    output wire       last
);

    wire        last_t;
    wire        valid_t;
    wire        ready_t;
    wire [7:0]  data;

    // Master: clk, rst, newd, din, tready, tvalid, tdata, tlast
    axis_m m1 (
        .m_axis_aclk    (clk),
        .m_axis_aresetn (rst),
        .newd           (newd),
        .din            (din),
        .m_axis_tready  (ready_t),
        .m_axis_tvalid  (valid_t),
        .m_axis_tdata   (data),
        .m_axis_tlast   (last_t)
    );

    // Slave: clk, rst, tready, tvalid, tdata, tlast, dout
    axis_s s1 (
        .s_axis_aclk    (clk),
        .s_axis_aresetn (rst),
        .s_axis_tready  (ready_t),
        .s_axis_tvalid  (valid_t),
        .s_axis_tdata   (data),
        .s_axis_tlast   (last_t),
        .dout           (dout)
    );

    assign last = last_t;

endmodule
