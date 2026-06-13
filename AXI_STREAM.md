# AXI4-Stream Data-Path IP — Master, Slave, FIFO & Top Integration

A compact, synthesizable **AMBA AXI4-Stream** data-path written in SystemVerilog,
comprising a streaming **master**, a streaming **slave**, a packet-aware
**synchronous FIFO**, and a **top-level** that wires the master to the slave.
This page documents the architecture, cycle-accurate behaviour, and design
trade-offs, with annotated block diagrams and animated waveforms.

<p align="center">
  <img src="figures/anim_axis_top.gif" alt="AXI4-Stream master-to-slave handshake animation" width="820"/>
</p>

---

## Table of Contents
1. [Overview](#1-overview)
2. [AXI4-Stream in a Nutshell](#2-axi4-stream-in-a-nutshell)
3. [Top-Level Integration](#3-top-level-integration)
4. [AXI4-Stream Master (`axis_m`)](#4-axi4-stream-master-axis_m)
5. [AXI4-Stream Slave (`axis_s`)](#5-axi4-stream-slave-axis_s)
6. [AXI4-Stream FIFO (`axis_fifo`)](#6-axi4-stream-fifo-axis_fifo)
7. [Signal Reference](#7-signal-reference)
8. [Design Notes, Limitations & Fixes](#8-design-notes-limitations--fixes)
9. [Repository Layout](#9-repository-layout)
10. [How the Figures Are Generated](#10-how-the-figures-are-generated)

---

## 1. Overview

The **AXI4-Stream** protocol is a lightweight, unidirectional, point-to-point
interface for moving data with **no address phase**. It is ideal for streaming
workloads — video pixels, DSP samples, packet payloads — where data flows
continuously from a producer (**master**) to a consumer (**slave**) using a
simple `TVALID` / `TREADY` handshake.

This IP demonstrates the three canonical building blocks of a streaming
sub-system:

| Block | Role | File |
|-------|------|------|
| `axis_m`    | Produces a 4-beat stream on demand | [`axis_m.sv`](#4-axi4-stream-master-axis_m) |
| `axis_s`    | Receives and exposes the stream    | [`axis_s.sv`](#5-axi4-stream-slave-axis_s) |
| `axis_fifo` | Packet-aware elastic buffer        | [`axis_fifo.sv`](#6-axi4-stream-fifo-axis_fifo) |
| `top`       | Connects master → slave            | [`top.sv`](#3-top-level-integration) |

---

## 2. AXI4-Stream in a Nutshell

A transfer happens on a rising clock edge **only when `TVALID` and `TREADY`
are both high** (the classic AXI handshake). Key sideband signals:

| Signal | Direction | Meaning |
|--------|-----------|---------|
| `TVALID` | Master → Slave | Master is presenting valid data |
| `TREADY` | Slave → Master | Slave can accept data this cycle |
| `TDATA`  | Master → Slave | Payload (here 8-bit) |
| `TLAST`  | Master → Slave | Marks the final beat of a packet |
| `TKEEP`  | Master → Slave | Byte-qualifier (valid byte indicator) |

> **Golden rule:** once `TVALID` is asserted it must stay asserted (with stable
> `TDATA`) until the handshake completes. `TREADY` may toggle freely to apply
> back-pressure.

---

## 3. Top-Level Integration

The `top` module instantiates the master and slave and connects them with four
internal wires — three forward (`data`, `valid_t`, `last_t`) and one backward
(`ready_t`).

```systemverilog
module top (
    input        clk, rst, newd,
    input  [7:0] din,
    output [7:0] dout,
    output       last
);
    wire last_t, valid_t, ready_t;
    wire [7:0] data;

    axis_m m1 (clk, rst, newd, din, ready_t, valid_t, data, last_t);
    axis_s s1 (clk, rst, ready_t, valid_t, data, last_t, dout);

    assign last = last_t;
endmodule
```

### Block diagram
![Top-level integration block diagram](figures/diagram_axis_top.png)

### Cycle-accurate handshake (animated)
The animation below shows both FSMs running together. A data **token** crosses
the channel on every accepted beat; the combined waveform strip tracks every
signal cycle-by-cycle.

![Top-level handshake animation](figures/anim_axis_top.gif)

**Data flow:**
1. A `newd` pulse starts the master.
2. The master drives `valid_t` + `data`; the slave replies with `ready_t`.
3. Four beats are streamed: `data = din × count` (count = 0 → 3).
4. `last_t` flags the 4th (final) beat and is exported as `last`.
5. The slave forwards each accepted byte to `dout`.

---

## 4. AXI4-Stream Master (`axis_m`)

A 2-state FSM (`IDLE`/`TX`) that emits **four beats** per `newd` pulse,
respecting the slave's `TREADY` back-pressure and asserting `TLAST` on the
final beat.

```systemverilog
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
    typedef enum bit {idle = 1'b0, tx = 1'b1} state_type;
    state_type state = idle, next_state = idle;
    reg [2:0] count = 0;

    // next-state logic
    always @(*) begin
        case (state)
            idle: next_state = newd ? tx : idle;
            tx:   next_state = (m_axis_tready && count == 3) ? idle : tx;
            default: next_state = idle;
        endcase
    end

    // state register
    always @(posedge m_axis_aclk)
        state <= (m_axis_aresetn == 1'b0) ? idle : next_state;

    // beat counter
    always @(posedge m_axis_aclk) begin
        if (state == idle)
            count <= 0;
        else if (state == tx && count != 3 && m_axis_tready)
            count <= count + 1;
    end

    assign m_axis_tvalid = (state == tx);
    assign m_axis_tdata  = m_axis_tvalid ? din * count : 8'h00;
    assign m_axis_tlast  = (count == 3 && state == tx);
endmodule
```

### Structure
![Master block diagram and FSM](figures/diagram_axis_master.png)

### Cycle-accurate operation (animated)
The GIF highlights the active FSM state, the live `count` register, the
combinational `tdata = din × count`, the handshake lamps, and a 7-signal
waveform — including a deliberate **back-pressure stall** (`tready` low) to
show the master holding its beat.

![Master operation animation](figures/anim_axis_master.gif)

### Transaction table

| state | count | tvalid | tdata  | tlast | comment |
|-------|-------|--------|--------|-------|---------|
| IDLE  | 0     | 0      | 0      | 0     | waiting for `newd` |
| TX    | 0     | 1      | din×0  | 0     | beat 0 (tready → count++) |
| TX    | 1     | 1      | din×1  | 0     | beat 1 |
| TX    | 2     | 1      | din×2  | 0     | beat 2 |
| TX    | 3     | 1      | din×3  | **1** | **LAST** → back to IDLE |

---

## 5. AXI4-Stream Slave (`axis_s`)

A simple receiver that asserts `TREADY` while in `STORE`, passes the incoming
`TDATA` straight to `dout`, and returns to `IDLE` on `TLAST`.

```systemverilog
module axis_s (
    input  wire       s_axis_aclk,
    input  wire       s_axis_aresetn,
    output wire       s_axis_tready,
    input  wire       s_axis_tvalid,
    input  wire [7:0] s_axis_tdata,
    input  wire       s_axis_tlast,
    output wire [7:0] dout
);
    typedef enum bit [1:0] {idle = 2'b00, store = 2'b01} state_type;
    state_type state = idle, next_state = idle;

    always @(posedge s_axis_aclk)
        state <= (s_axis_aresetn == 1'b0) ? idle : next_state;

    always @(*) begin
        case (state)
            idle:  next_state = s_axis_tvalid ? store : idle;
            store: next_state = (s_axis_tlast && s_axis_tvalid) ? idle :
                                (s_axis_tvalid ? store : idle);
            default: next_state = idle;
        endcase
    end

    assign s_axis_tready = (state == store);
    assign dout          = (state == store) ? s_axis_tdata : 8'h00;
endmodule
```

### Structure
![Slave block diagram and FSM](figures/diagram_axis_slave.png)

### Cycle-accurate operation (animated)
![Slave operation animation](figures/anim_axis_slave.gif)

### Capture table

| state | tvalid | tlast | tready | dout  | comment |
|-------|--------|-------|--------|-------|---------|
| IDLE  | 0      | –     | 0      | 0     | idle, no data |
| IDLE  | 1      | 0     | 0      | 0     | request seen → STORE |
| STORE | 1      | 0     | 1      | tdata | capture byte |
| STORE | 1      | 0     | 1      | tdata | capture byte |
| STORE | 1      | 1     | 1      | tdata | **LAST** byte → IDLE |

---

## 6. AXI4-Stream FIFO (`axis_fifo`)

A 16-deep **synchronous** FIFO that buffers `TDATA`, `TKEEP`, and `TLAST`
together so packet framing is preserved end-to-end. It decouples an upstream
slave from a downstream mux master (rate matching / elasticity).

```systemverilog
module axis_fifo (
    input  wire       aclk, aresetn,
    input  wire       s_axis_tvalid,
    input  wire [7:0] s_axis_tdata,
    input  wire       s_axis_tkeep,
    input  wire       s_axis_tlast,
    output reg        m_axis_tvalid,
    output reg  [7:0] m_axis_tdata,
    output reg        m_axis_tkeep,
    output reg        m_axis_tlast,
    input  wire       m_axis_tready
);
    reg [7:0] mem_d [16];
    reg       mem_k [16];
    reg       mem_l [16];
    reg [4:0] wr_ptr, rd_ptr, count;

    wire full  = (count == 5'd15);
    wire empty = (count == 5'd0);

    always @(posedge aclk) begin
        if (!aresetn) begin
            wr_ptr <= 0; rd_ptr <= 0; count <= 0;
            {m_axis_tvalid, m_axis_tkeep, m_axis_tlast} <= 0;
            m_axis_tdata <= 8'h00;
        end
        else if (s_axis_tvalid && !full) begin       // WRITE (priority)
            mem_d[wr_ptr] <= s_axis_tdata;
            mem_k[wr_ptr] <= s_axis_tkeep;
            mem_l[wr_ptr] <= s_axis_tlast;
            wr_ptr <= wr_ptr + 1; count <= count + 1;
            m_axis_tvalid <= 1'b0;
        end
        else if (m_axis_tready && !empty) begin       // READ
            m_axis_tdata  <= mem_d[rd_ptr];
            m_axis_tkeep  <= mem_k[rd_ptr];
            m_axis_tlast  <= mem_l[rd_ptr];
            m_axis_tvalid <= 1'b1;
            rd_ptr <= rd_ptr + 1; count <= count - 1;
        end
    end
endmodule
```

### Structure
![FIFO block diagram, circular buffer and decision logic](figures/diagram_axis_fifo.png)

### Cycle-accurate operation (animated)
The animation shows the **circular buffer** filling with data, the `wr_ptr` /
`rd_ptr` moving around the ring, the occupancy gauge, the `full` / `empty`
lamps, and the read/write waveforms. The stimulus includes overlapping
read+write requests to highlight the **write-priority** behaviour.

![FIFO operation animation](figures/anim_axis_fifo.gif)

### Per-clock decision (priority)

```
posedge aclk
 ├─ !aresetn                 → reset pointers/count, zero memory
 ├─ else if tvalid && !full  → WRITE  (wr_ptr++, count++)
 └─ else if tready && !empty → READ   (rd_ptr++, count--)
```

`full = (count == 15)`, `empty = (count == 0)`. Only **one** action occurs per
clock edge.

---

## 7. Signal Reference

### Internal wires of `top`

| Wire        | Driven by (master) | Consumed by (slave) | Direction |
|-------------|--------------------|---------------------|-----------|
| `data[7:0]` | `m_axis_tdata`     | `s_axis_tdata`      | M → S |
| `valid_t`   | `m_axis_tvalid`    | `s_axis_tvalid`     | M → S |
| `last_t`    | `m_axis_tlast`     | `s_axis_tlast`      | M → S |
| `ready_t`   | `m_axis_tready`    | `s_axis_tready`     | S → M |

---

## 8. Design Notes, Limitations & Fixes

These observations make good discussion points for a conference / review.

### Master (`axis_m`)
- ✔ First beat carries `din × 0 = 0` (by design — `count` starts at 0). If a
  non-zero first beat is desired, pre-increment `count` or seed it at 1.
- ⚠ In the original source the `count` register and the sequential `always`
  blocks were written **inside** the combinational `case` — illegal SystemVerilog.
  The version above moves them to module scope (correct & synthesizable).

### Slave (`axis_s`)
- ⚠ **One-cycle handshake latency:** `TREADY` is only high *during* `STORE`,
  which is entered the cycle *after* `TVALID` is first seen. A strict AXIS
  slave usually drives `TREADY` combinationally so the first beat is not
  dropped.
- The unused `last_byte` state from the original was removed as dead code.
- `dout` is a combinational mirror of `TDATA` (not a registered capture).

### FIFO (`axis_fifo`)
- ⚠ **Read and write are mutually exclusive** (chained `else if`) — only one
  per cycle, halving throughput and risking overflow under sustained traffic.
  A true FIFO services both in the same cycle.
- ⚠ **No `s_axis_tready` output** — the slave side cannot back-pressure the
  upstream master, so data is lost when `full`.
- ⚠ **Pointer width vs. depth:** 5-bit `wr_ptr`/`rd_ptr` increment freely and
  can index **out of range** of the `[16]` arrays. Mask to 4 bits
  (`wr_ptr[3:0]`) or wrap explicitly. Also `full` at `count == 15` wastes one
  slot (effective depth 15).
- ⚠ `m_axis_tvalid` is cleared on write cycles, creating read-side bubbles.

---

## 9. Repository Layout

```
.
├── AXI_STREAM.md                     ← this page
├── figures/
│   ├── diagram_axis_master.png       ← master block diagram
│   ├── diagram_axis_slave.png        ← slave block diagram
│   ├── diagram_axis_top.png          ← top integration diagram
│   ├── diagram_axis_fifo.png         ← FIFO structure diagram
│   ├── anim_axis_master.gif          ← master cycle-accurate animation
│   ├── anim_axis_slave.gif           ← slave cycle-accurate animation
│   ├── anim_axis_top.gif             ← top handshake animation
│   └── anim_axis_fifo.gif            ← FIFO cycle-accurate animation
├── generate_axis_master_diagram.py
├── generate_axis_slave_diagram.py
├── generate_axis_top_diagram.py
├── generate_axis_fifo_diagram.py
├── generate_axis_master_gif.py
├── generate_axis_slave_gif.py
├── generate_axis_top_gif.py
└── generate_axis_fifo_gif.py
```

---

## 10. How the Figures Are Generated

All diagrams and animations are produced programmatically with
**Matplotlib + Pillow** from behavioural models that reproduce the RTL exactly
(same FSM transitions and output equations), so every waveform is
cycle-accurate.

```bash
# static block diagrams
python generate_axis_master_diagram.py
python generate_axis_slave_diagram.py
python generate_axis_top_diagram.py
python generate_axis_fifo_diagram.py

# animated GIFs (each frame = one clock cycle)
python generate_axis_master_gif.py
python generate_axis_slave_gif.py
python generate_axis_top_gif.py
python generate_axis_fifo_gif.py
```

**Dependencies:** `matplotlib`, `numpy`, `pillow`.

```bash
pip install matplotlib numpy pillow
```

---

<p align="center"><i>AMBA® and AXI® are registered trademarks of Arm Limited.</i></p>
