// =============================================================================
//  axis_fifo.sv  —  AXI4-Stream Synchronous FIFO (16-deep)
// -----------------------------------------------------------------------------
//  Buffers TDATA / TKEEP / TLAST together so packet framing is preserved while
//  decoupling an upstream slave port from a downstream master (mux) port.
//
//  NOTE: This is the design as submitted. See README "Design Notes" for known
//        limitations (write-priority mutual exclusion, no slave-side TREADY,
//        pointer-width vs. depth). A hardened variant is left as future work.
// =============================================================================
module axis_fifo (
    input  wire       aclk,
    input  wire       aresetn,

    // Slave (write) port
    input  wire       s_axis_tvalid,
    input  wire [7:0] s_axis_tdata,
    input  wire       s_axis_tkeep,
    input  wire       s_axis_tlast,

    // Master (read) port  -> to mux
    output reg        m_axis_tvalid,
    output reg  [7:0] m_axis_tdata,
    output reg        m_axis_tkeep,
    output reg        m_axis_tlast,
    input  wire       m_axis_tready
);

    localparam int DEPTH = 16;

    reg [7:0] mem_d [DEPTH];
    reg       mem_k [DEPTH];
    reg       mem_l [DEPTH];

    reg [4:0] wr_ptr;
    reg [4:0] rd_ptr;
    reg [4:0] count;

    wire full  = (count == 5'd15);
    wire empty = (count == 5'd0);

    always @(posedge aclk) begin
        if (!aresetn) begin
            wr_ptr        <= 5'd0;
            rd_ptr        <= 5'd0;
            count         <= 5'd0;
            m_axis_tvalid <= 1'b0;
            m_axis_tkeep  <= 1'b0;
            m_axis_tlast  <= 1'b0;
            m_axis_tdata  <= 8'h00;
            for (int i = 0; i < DEPTH; i++) begin
                mem_d[i] <= 8'h00;
                mem_k[i] <= 1'b0;
                mem_l[i] <= 1'b0;
            end
        end
        // WRITE has priority over READ
        else if (s_axis_tvalid && !full) begin
            mem_d[wr_ptr] <= s_axis_tdata;
            mem_k[wr_ptr] <= s_axis_tkeep;
            mem_l[wr_ptr] <= s_axis_tlast;
            wr_ptr        <= wr_ptr + 5'd1;
            count         <= count  + 5'd1;
            m_axis_tvalid <= 1'b0;
            m_axis_tkeep  <= 1'b0;
            m_axis_tlast  <= 1'b0;
            m_axis_tdata  <= 8'h00;
        end
        // READ when consumer is ready and FIFO is not empty
        else if (m_axis_tready && !empty) begin
            m_axis_tdata  <= mem_d[rd_ptr];
            m_axis_tkeep  <= mem_k[rd_ptr];
            m_axis_tlast  <= mem_l[rd_ptr];
            m_axis_tvalid <= 1'b1;
            rd_ptr        <= rd_ptr + 5'd1;
            count         <= count  - 5'd1;
        end
    end

endmodule
