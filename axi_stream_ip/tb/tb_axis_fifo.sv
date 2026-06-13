// =============================================================================
//  tb_axis_fifo.sv  —  Testbench for the AXI4-Stream FIFO
// -----------------------------------------------------------------------------
//  Writes a short burst then drains it, printing every write and read.
//      iverilog -g2012 rtl/axis_fifo.sv tb/tb_axis_fifo.sv && vvp a.out
// =============================================================================
`timescale 1ns/1ps

module tb_axis_fifo;

    logic        aclk;
    logic        aresetn;     // active-low
    logic        s_axis_tvalid;
    logic [7:0]  s_axis_tdata;
    logic        s_axis_tkeep;
    logic        s_axis_tlast;
    logic        m_axis_tvalid;
    logic [7:0]  m_axis_tdata;
    logic        m_axis_tkeep;
    logic        m_axis_tlast;
    logic        m_axis_tready;

    axis_fifo dut (
        .aclk          (aclk),
        .aresetn       (aresetn),
        .s_axis_tvalid (s_axis_tvalid),
        .s_axis_tdata  (s_axis_tdata),
        .s_axis_tkeep  (s_axis_tkeep),
        .s_axis_tlast  (s_axis_tlast),
        .m_axis_tvalid (m_axis_tvalid),
        .m_axis_tdata  (m_axis_tdata),
        .m_axis_tkeep  (m_axis_tkeep),
        .m_axis_tlast  (m_axis_tlast),
        .m_axis_tready (m_axis_tready)
    );

    initial aclk = 1'b0;
    always #5 aclk = ~aclk;

    integer k;
    initial begin
        $dumpfile("tb_axis_fifo.vcd");
        $dumpvars(0, tb_axis_fifo);

        aresetn       = 1'b0;
        s_axis_tvalid = 1'b0;
        s_axis_tdata  = 8'h00;
        s_axis_tkeep  = 1'b1;
        s_axis_tlast  = 1'b0;
        m_axis_tready = 1'b0;
        repeat (3) @(posedge aclk);
        aresetn = 1'b1;

        // ---- Write 6 beats (10,20,...,60), last on the final beat ----
        for (k = 1; k <= 6; k++) begin
            @(posedge aclk);
            s_axis_tvalid = 1'b1;
            s_axis_tdata  = k * 10;
            s_axis_tlast  = (k == 6);
        end
        @(posedge aclk);
        s_axis_tvalid = 1'b0;
        s_axis_tlast  = 1'b0;

        // ---- Drain via reads ----
        @(posedge aclk);
        m_axis_tready = 1'b1;
        repeat (10) @(posedge aclk);
        m_axis_tready = 1'b0;

        repeat (2) @(posedge aclk);
        $finish;
    end

    always @(posedge aclk) begin
        if (m_axis_tvalid)
            $display("[%0t] READ  data=%0d last=%0b", $time, m_axis_tdata, m_axis_tlast);
    end

endmodule
