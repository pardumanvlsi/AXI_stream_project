// =============================================================================
//  axis_s.sv  —  AXI4-Stream Slave
// -----------------------------------------------------------------------------
//  Receives a stream, asserting TREADY while in STORE and exposing the incoming
//  TDATA on `dout`. Returns to IDLE when the final beat (TLAST) is accepted.
// =============================================================================
module axis_s (
    input  wire       s_axis_aclk,
    input  wire       s_axis_aresetn,
    output wire       s_axis_tready,
    input  wire       s_axis_tvalid,
    input  wire [7:0] s_axis_tdata,
    input  wire       s_axis_tlast,
    output wire [7:0] dout
);

    typedef enum bit [1:0] {IDLE = 2'b00, STORE = 2'b01} state_type;
    state_type state = IDLE, next_state = IDLE;

    // -------------------------------------------------------------------------
    // State register
    // -------------------------------------------------------------------------
    always @(posedge s_axis_aclk) begin
        if (!s_axis_aresetn)
            state <= IDLE;
        else
            state <= next_state;
    end

    // -------------------------------------------------------------------------
    // Next-state logic (combinational)
    // -------------------------------------------------------------------------
    always @(*) begin
        case (state)
            IDLE:  next_state = s_axis_tvalid ? STORE : IDLE;
            STORE: begin
                if (s_axis_tlast && s_axis_tvalid)
                    next_state = IDLE;
                else if (s_axis_tvalid)
                    next_state = STORE;
                else
                    next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    // -------------------------------------------------------------------------
    // Outputs
    // -------------------------------------------------------------------------
    assign s_axis_tready = (state == STORE);
    assign dout          = (state == STORE) ? s_axis_tdata : 8'h00;

endmodule
