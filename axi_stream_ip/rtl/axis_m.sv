// =============================================================================
//  axis_m.sv  —  AXI4-Stream Master
// -----------------------------------------------------------------------------
//  Emits a 4-beat stream (count = 0..3) on each `newd` pulse, honouring the
//  downstream TREADY back-pressure and asserting TLAST on the final beat.
//
//  tdata = din * count   (first beat carries din*0 = 0 by design)
// =============================================================================
module axis_m (
    input  wire       m_axis_aclk,
    input  wire       m_axis_aresetn,
    input  wire       newd,
    input  wire [7:0] din,
    input  wire       m_axis_tready,
    output wire       m_axis_tvalid,
    output wire [7:0] m_axis_tdata,
    output wire       m_axis_tlast
);

    typedef enum bit {IDLE = 1'b0, TX = 1'b1} state_type;
    state_type state = IDLE, next_state = IDLE;

    reg [2:0] count = 3'd0;

    // -------------------------------------------------------------------------
    // Next-state logic (combinational)
    // -------------------------------------------------------------------------
    always @(*) begin
        case (state)
            IDLE: next_state = newd ? TX : IDLE;
            TX:   next_state = (m_axis_tready && count == 3'd3) ? IDLE : TX;
            default: next_state = IDLE;
        endcase
    end

    // -------------------------------------------------------------------------
    // State register
    // -------------------------------------------------------------------------
    always @(posedge m_axis_aclk) begin
        if (!m_axis_aresetn)
            state <= IDLE;
        else
            state <= next_state;
    end

    // -------------------------------------------------------------------------
    // Beat counter
    // -------------------------------------------------------------------------
    always @(posedge m_axis_aclk) begin
        if (state == IDLE)
            count <= 3'd0;
        else if (state == TX && count != 3'd3 && m_axis_tready)
            count <= count + 3'd1;
    end

    // -------------------------------------------------------------------------
    // Outputs (combinational)
    // -------------------------------------------------------------------------
    assign m_axis_tvalid = (state == TX);
    assign m_axis_tdata  = m_axis_tvalid ? (din * count) : 8'h00;
    assign m_axis_tlast  = (state == TX && count == 3'd3);

endmodule
