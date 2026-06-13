<h1 align="center">AXI4-Stream Data-Path IP</h1>

<p align="center">
  <em>A compact, synthesizable AMBA® AXI4-Stream data path in SystemVerilog —
  streaming master, slave, packet-aware FIFO, and top-level integration.</em>
</p>

<p align="center">
  <img alt="Language" src="https://img.shields.io/badge/HDL-SystemVerilog-blue.svg">
  <img alt="Protocol" src="https://img.shields.io/badge/Protocol-AXI4--Stream-orange.svg">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg">
  <img alt="Status" src="https://img.shields.io/badge/Status-Educational-lightgrey.svg">
</p>

<p align="center">
  <img src="figures/anim_axis_top.gif" alt="AXI4-Stream master-to-slave handshake animation" width="840"/>
</p>

---

## ✨ Highlights

- **Four building blocks** of a streaming sub-system: master, slave, FIFO, top.
- **Cycle-accurate animations** for every module (each frame = one clock cycle).
- **Annotated block diagrams** generated programmatically and reproducible.
- **Self-contained** — RTL, testbenches, figures, and the scripts that build them.

---

## 📑 Table of Contents

1. [Overview](#-overview)
2. [AXI4-Stream in a Nutshell](#-axi4-stream-in-a-nutshell)
3. [Repository Layout](#-repository-layout)
4. [Top-Level Integration](#-top-level-integration)
5. [AXI4-Stream Master](#-axi4-stream-master-axis_m)
6. [AXI4-Stream Slave](#-axi4-stream-slave-axis_s)
7. [AXI4-Stream FIFO](#-axi4-stream-fifo-axis_fifo)
8. [Signal Reference](#-signal-reference)
9. [Design Notes, Limitations & Future Work](#-design-notes-limitations--future-work)
10. [Simulation](#-simulation)
11. [Regenerating the Figures](#-regenerating-the-figures)
12. [License](#-license)

---

## 📖 Overview

**AXI4-Stream** is a lightweight, unidirectional, point-to-point AMBA interface
for moving data with **no address phase**. It suits streaming workloads — video
pixels, DSP samples, packet payloads — where data flows continuously from a
producer (**master**) to a consumer (**slave**) over a simple
`TVALID` / `TREADY` handshake.

This IP demonstrates the canonical streaming blocks:

| Block | Role | Source |
|-------|------|--------|
| `axis_m`    | Produces a 4-beat stream on demand | [`rtl/axis_m.sv`](rtl/axis_m.sv) |
| `axis_s`    | Receives and exposes the stream    | [`rtl/axis_s.sv`](rtl/axis_s.sv) |
| `axis_fifo` | Packet-aware elastic buffer        | [`rtl/axis_fifo.sv`](rtl/axis_fifo.sv) |
| `top`       | Connects master → slave            | [`rtl/top.sv`](rtl/top.sv) |

---

## 🔁 AXI4-Stream in a Nutshell

A transfer happens on a rising clock edge **only when `TVALID` and `TREADY` are
both high** (the classic AXI handshake).

| Signal | Direction | Meaning |
|--------|-----------|---------|
| `TVALID` | Master → Slave | Master is presenting valid data |
| `TREADY` | Slave → Master | Slave can accept data this cycle |
| `TDATA`  | Master → Slave | Payload (8-bit here) |
| `TLAST`  | Master → Slave | Marks the final beat of a packet |
| `TKEEP`  | Master → Slave | Byte qualifier (valid-byte indicator) |

> **Golden rule:** once `TVALID` is asserted it must remain asserted, with stable
> `TDATA`, until the handshake completes. `TREADY` may toggle freely to apply
> back-pressure.

---

## 🗂 Repository Layout

```
axi_stream_ip/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── rtl/                        # synthesizable SystemVerilog
│   ├── axis_m.sv               #   streaming master
│   ├── axis_s.sv               #   streaming slave
│   ├── axis_fifo.sv            #   16-deep packet FIFO
│   └── top.sv                  #   master → slave integration
├── tb/                         # testbenches
│   ├── tb_axis_top.sv
│   └── tb_axis_fifo.sv
├── figures/                    # diagrams + animations
│   ├── diagram_axis_*.png
│   └── anim_axis_*.gif
└── scripts/                    # Python figure generators (Matplotlib)
    ├── generate_axis_*_diagram.py
    └── generate_axis_*_gif.py
```

---

## 🔗 Top-Level Integration

The `top` module instantiates the master and slave and connects them with four
internal wires — three forward (`data`, `valid_t`, `last_t`) and one backward
(`ready_t`).

```systemverilog
axis_m m1 (clk, rst, newd, din, ready_t, valid_t, data, last_t);
axis_s s1 (clk, rst, ready_t, valid_t, data, last_t, dout);
assign last = last_t;
```

### Block diagram
![Top-level integration block diagram](figures/diagram_axis_top.png)

### Cycle-accurate handshake
Both FSMs run together; a data **token** crosses the channel on every accepted
beat, and the combined waveform strip tracks each signal per cycle.

![Top-level handshake animation](figures/anim_axis_top.gif)

**Data flow**
1. A `newd` pulse starts the master.
2. The master drives `valid_t` + `data`; the slave replies with `ready_t`.
3. Four beats stream: `data = din × count` (count = 0 → 3).
4. `last_t` flags the 4th (final) beat and is exported as `last`.
5. The slave forwards each accepted byte to `dout`.

---

## 📤 AXI4-Stream Master (`axis_m`)

A 2-state FSM (`IDLE` / `TX`) that emits **four beats** per `newd` pulse,
respecting `TREADY` back-pressure and asserting `TLAST` on the final beat.

### Structure
![Master block diagram and FSM](figures/diagram_axis_master.png)

### Cycle-accurate operation
Highlights the active state, the live `count`, the combinational
`tdata = din × count`, the handshake lamps, and a 7-signal waveform — including
a deliberate **back-pressure stall**.

![Master operation animation](figures/anim_axis_master.gif)

### Transaction table

| state | count | tvalid | tdata  | tlast | comment |
|-------|-------|--------|--------|-------|---------|
| IDLE  | 0     | 0      | 0      | 0     | waiting for `newd` |
| TX    | 0     | 1      | din×0  | 0     | beat 0 (tready → count++) |
| TX    | 1     | 1      | din×1  | 0     | beat 1 |
| TX    | 2     | 1      | din×2  | 0     | beat 2 |
| TX    | 3     | 1      | din×3  | **1** | **LAST** → back to IDLE |

> Full source: [`rtl/axis_m.sv`](rtl/axis_m.sv)

---

## 📥 AXI4-Stream Slave (`axis_s`)

Asserts `TREADY` while in `STORE`, passes incoming `TDATA` to `dout`, and
returns to `IDLE` when `TLAST` is accepted.

### Structure
![Slave block diagram and FSM](figures/diagram_axis_slave.png)

### Cycle-accurate operation
![Slave operation animation](figures/anim_axis_slave.gif)

### Capture table

| state | tvalid | tlast | tready | dout  | comment |
|-------|--------|-------|--------|-------|---------|
| IDLE  | 0      | –     | 0      | 0     | idle, no data |
| IDLE  | 1      | 0     | 0      | 0     | request seen → STORE |
| STORE | 1      | 0     | 1      | tdata | capture byte |
| STORE | 1      | 0     | 1      | tdata | capture byte |
| STORE | 1      | 1     | 1      | tdata | **LAST** byte → IDLE |

> Full source: [`rtl/axis_s.sv`](rtl/axis_s.sv)

---

## 🧮 AXI4-Stream FIFO (`axis_fifo`)

A 16-deep **synchronous** FIFO that buffers `TDATA`, `TKEEP`, and `TLAST`
together so packet framing is preserved, decoupling an upstream slave from a
downstream mux master (rate matching / elasticity).

### Structure
![FIFO block diagram, circular buffer and decision logic](figures/diagram_axis_fifo.png)

### Cycle-accurate operation
Shows the circular buffer filling, the `wr_ptr` / `rd_ptr` moving around the
ring, the occupancy gauge, the `full` / `empty` lamps, and the read/write
waveforms. The stimulus includes overlapping read+write requests to highlight
the **write-priority** behaviour.

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

> Full source: [`rtl/axis_fifo.sv`](rtl/axis_fifo.sv)

---

## 🧷 Signal Reference

### Internal wires of `top`

| Wire        | Driven by (master) | Consumed by (slave) | Direction |
|-------------|--------------------|---------------------|-----------|
| `data[7:0]` | `m_axis_tdata`     | `s_axis_tdata`      | M → S |
| `valid_t`   | `m_axis_tvalid`    | `s_axis_tvalid`     | M → S |
| `last_t`    | `m_axis_tlast`     | `s_axis_tlast`      | M → S |
| `ready_t`   | `m_axis_tready`    | `s_axis_tready`     | S → M |

---

## 🛠 Design Notes, Limitations & Future Work

These are deliberate discussion points (useful for review / conference Q&A).

### Master (`axis_m`)
- ✔ The first beat carries `din × 0 = 0` by design (`count` starts at 0). Seed
  `count` at 1 if a non-zero first beat is required.

### Slave (`axis_s`)
- ⚠ **One-cycle handshake latency:** `TREADY` is asserted only *in* `STORE`,
  which is entered the cycle *after* `TVALID` is first seen. A strict AXIS slave
  usually drives `TREADY` combinationally so the first beat is not dropped.
- `dout` is a combinational mirror of `TDATA`, not a registered capture.

### FIFO (`axis_fifo`)
- ⚠ **Read and write are mutually exclusive** (chained `else if`) — only one
  per cycle, halving throughput. A production FIFO services both simultaneously.
- ⚠ **No `s_axis_tready` output** — the slave side cannot back-pressure the
  upstream master, so data is lost when `full`.
- ⚠ **Pointer width vs. depth:** 5-bit pointers increment freely and can index
  beyond the `[16]` arrays; mask to 4 bits (`wr_ptr[3:0]`) or wrap explicitly.
  Also `full` at `count == 15` leaves one slot unused (effective depth 15).
- ⚠ `m_axis_tvalid` is cleared on write cycles, creating read-side bubbles.

---

## 🧪 Simulation

Any SystemVerilog-2012 simulator works. Examples:

**Icarus Verilog**
```bash
# Top integration
iverilog -g2012 -o sim_top rtl/axis_m.sv rtl/axis_s.sv rtl/top.sv tb/tb_axis_top.sv
vvp sim_top

# FIFO
iverilog -g2012 -o sim_fifo rtl/axis_fifo.sv tb/tb_axis_fifo.sv
vvp sim_fifo
```

**Xilinx Vivado (xsim)**
```bash
xvlog -sv rtl/*.sv tb/tb_axis_top.sv
xelab -debug typical tb_axis_top -s top_sim
xsim top_sim -runall
```

Waveforms are dumped to `*.vcd` (view with GTKWave / Vivado).

---

## 🎬 Regenerating the Figures

All diagrams and animations are produced programmatically with
**Matplotlib + Pillow** from behavioural models that reproduce the RTL exactly,
so every waveform is cycle-accurate.

```bash
pip install -r requirements.txt

# static block diagrams
python scripts/generate_axis_master_diagram.py
python scripts/generate_axis_slave_diagram.py
python scripts/generate_axis_top_diagram.py
python scripts/generate_axis_fifo_diagram.py

# animated GIFs (each frame = one clock cycle)
python scripts/generate_axis_master_gif.py
python scripts/generate_axis_slave_gif.py
python scripts/generate_axis_top_gif.py
python scripts/generate_axis_fifo_gif.py
```

Outputs are written to [`figures/`](figures/).

---

## 📜 License

Released under the [MIT License](LICENSE).

<p align="center"><sub>AMBA® and AXI® are registered trademarks of Arm Limited.</sub></p>
