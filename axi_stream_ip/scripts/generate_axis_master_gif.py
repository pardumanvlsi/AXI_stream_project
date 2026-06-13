"""Cycle-accurate animated GIF for the AXI4-Stream MASTER (axis_m).

Renders a publication-quality animation suitable for an international
conference slide. Each frame = one clock cycle. The figure shows:
  * a live FSM (IDLE / TX) with the active state highlighted
  * the datapath (count register, din, tdata = din*count)
  * a scrolling digital-waveform pane for clk, newd, tready,
    tvalid, tdata, tlast, count

The waveform values come from a small behavioural model that reproduces
the intended behaviour of the RTL (4 beats per `newd`, tlast on count==3).

Output: figures/anim_axis_master.gif
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.animation import FuncAnimation, PillowWriter

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(exist_ok=True)

PRIMARY = "#1f4e79"
ACCENT = "#c00000"
GREEN = "#2e7d32"
AMBER = "#b8860b"
LIGHT = "#deebf7"
LIGHT3 = "#e2efda"
PINK = "#fce4d6"
GREY = "#888888"
DK = "#222222"
DIN_VAL = 5  # din held constant at 5 for a clean demo


# --------------------------------------------------------------------------
# 1. Behavioural model: produce per-cycle signal values
# --------------------------------------------------------------------------
def simulate(n_cycles=22):
    """Return list of per-cycle dicts mirroring axis_m behaviour."""
    # Stimulus: newd pulse high at cycle 2; tready high from cycle 3 with a
    # one-cycle stall at cycle 6 to show back-pressure.
    newd = [0] * n_cycles
    newd[2] = 1
    tready = [0] * n_cycles
    for c in range(3, n_cycles):
        tready[c] = 1
    tready[6] = 0  # back-pressure bubble

    state = "IDLE"
    count = 0
    rows = []
    for c in range(n_cycles):
        # ---- combinational outputs for current state/count ----
        tvalid = 1 if state == "TX" else 0
        tdata = (DIN_VAL * count) if tvalid else 0
        tlast = 1 if (count == 3 and state == "TX") else 0
        rows.append(dict(cyc=c, newd=newd[c], tready=tready[c], state=state,
                         count=count, tvalid=tvalid, tdata=tdata, tlast=tlast))
        # ---- next-state / next-count (registered) ----
        nstate, ncount = state, count
        if state == "IDLE":
            ncount = 0
            if newd[c] == 1:
                nstate = "TX"
        else:  # TX
            if tready[c] == 1:
                if count != 3:
                    ncount = count + 1
                    nstate = "TX"
                else:
                    nstate = "IDLE"
            else:
                nstate = "TX"
        state, count = nstate, ncount
    return rows


SIG = simulate()
N = len(SIG)


# --------------------------------------------------------------------------
# 2. Drawing helpers
# --------------------------------------------------------------------------
def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=4)
    return p


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=1.8, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=15, linewidth=lw, color=color, zorder=2)
    ax.add_patch(a)


def draw_binary_wave(ax, y0, values, upto, *, color=DK, height=0.7, label=""):
    """Draw a 0/1 digital waveform up to index `upto` (inclusive)."""
    xs, ys = [], []
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        xs += [i, i + 1]
        ys += [y0 + (height if v else 0)] * 2
        if i > 0:  # vertical edge
            ax.plot([i, i], [y0 + (height if values[i - 1] else 0),
                             y0 + (height if v else 0)], color=color, lw=2, zorder=3)
    ax.plot(xs, ys, color=color, lw=2, zorder=3)


def draw_bus_wave(ax, y0, values, upto, *, color=PRIMARY, height=0.7):
    """Draw a multi-bit bus waveform (hex/decimal) up to `upto`."""
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        # bus envelope
        ax.plot([i, i + 1], [y0 + height, y0 + height], color=color, lw=1.6, zorder=3)
        ax.plot([i, i + 1], [y0, y0], color=color, lw=1.6, zorder=3)
        if i > 0 and values[i] != values[i - 1]:
            ax.plot([i, i], [y0, y0 + height], color=color, lw=1.6, zorder=3)
        ax.text(i + 0.5, y0 + height / 2, str(v), ha="center", va="center",
                fontsize=7.5, color=color, zorder=4)


# --------------------------------------------------------------------------
# 3. Figure scaffold
# --------------------------------------------------------------------------
fig = plt.figure(figsize=(13, 7.2))
fig.suptitle("AXI4-Stream Master (axis_m) — Cycle-Accurate Operation",
             fontsize=15, fontweight="bold", color=PRIMARY, y=0.985)

# left: FSM + datapath
axL = fig.add_axes([0.02, 0.06, 0.40, 0.84])
axL.set_xlim(0, 10)
axL.set_ylim(0, 10)
axL.axis("off")

# right: waveforms
axW = fig.add_axes([0.46, 0.10, 0.52, 0.78])
axW.set_xlim(0, N)
axW.set_ylim(0, 9.2)
axW.axis("off")
axW.set_title("Digital Waveforms", fontsize=12, fontweight="bold", color=PRIMARY)

WAVE_ROWS = [  # (label, key, kind)
    ("clk",    None,     "clk"),
    ("newd",   "newd",   "bin"),
    ("tready", "tready", "bin"),
    ("tvalid", "tvalid", "bin"),
    ("tdata",  "tdata",  "bus"),
    ("tlast",  "tlast",  "bin"),
    ("count",  "count",  "bus"),
]
ROW_Y = {name: 8.2 - i * 1.18 for i, (name, _, _) in enumerate(WAVE_ROWS)}


def render(frame):
    # ---------- LEFT: FSM + datapath ----------
    axL.clear()
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 10)
    axL.axis("off")
    s = SIG[frame]

    axL.text(5.0, 9.6, "FSM  &  Datapath", fontsize=12, fontweight="bold",
             color=PRIMARY, ha="center")

    active = s["state"]
    # IDLE
    idle_on = active == "IDLE"
    c1 = Circle((2.6, 7.4), 1.2,
                facecolor=ACCENT if idle_on else LIGHT,
                edgecolor=ACCENT if idle_on else PRIMARY,
                linewidth=3 if idle_on else 1.8, zorder=3)
    axL.add_patch(c1)
    axL.text(2.6, 7.4, "IDLE", ha="center", va="center", fontsize=12,
             fontweight="bold", color="white" if idle_on else DK, zorder=4)
    # TX
    tx_on = active == "TX"
    c2 = Circle((7.4, 7.4), 1.2,
                facecolor=GREEN if tx_on else LIGHT3,
                edgecolor=GREEN if tx_on else PRIMARY,
                linewidth=3 if tx_on else 1.8, zorder=3)
    axL.add_patch(c2)
    axL.text(7.4, 7.4, "TX", ha="center", va="center", fontsize=12,
             fontweight="bold", color="white" if tx_on else DK, zorder=4)

    # transitions
    arrow(axL, 3.8, 7.95, 6.2, 7.95, color=PRIMARY, conn="arc3,rad=-0.3")
    axL.text(5.0, 8.95, "newd==1", ha="center", fontsize=8.5, color=PRIMARY,
             fontweight="bold")
    arrow(axL, 6.2, 6.85, 3.8, 6.85, color=PRIMARY, conn="arc3,rad=-0.3")
    axL.text(5.0, 5.95, "tready & count==3", ha="center", fontsize=8.5,
             color=PRIMARY, fontweight="bold")

    # datapath boxes
    box(axL, 0.6, 3.4, 2.6, 1.0, f"din = {DIN_VAL}", fc=PINK, ec=ACCENT, fs=11, bold=True)
    box(axL, 3.7, 3.4, 2.6, 1.0, f"count = {s['count']}", fc="#fff2cc",
        ec=AMBER, fs=11, bold=True)
    box(axL, 6.8, 3.4, 2.6, 1.0, f"tdata = {s['tdata']}",
        fc=LIGHT3 if s["tvalid"] else "#f0f0f0",
        ec=GREEN if s["tvalid"] else GREY, fs=11, bold=True)
    arrow(axL, 3.2, 3.9, 3.7, 3.9, color=GREY)
    arrow(axL, 6.3, 3.9, 6.8, 3.9, color=GREY)
    axL.text(5.0, 2.95, "tdata = din \u00d7 count", ha="center", fontsize=9,
             color=DK, style="italic")

    # handshake status lamps
    def lamp(x, label, on, on_color):
        c = Circle((x, 1.5), 0.32, facecolor=on_color if on else "#dddddd",
                   edgecolor=DK, linewidth=1.2, zorder=3)
        axL.add_patch(c)
        axL.text(x, 0.75, label, ha="center", fontsize=8.5,
                 color=DK, fontweight="bold")
    lamp(1.6, "newd", s["newd"], ACCENT)
    lamp(3.6, "tready", s["tready"], GREEN)
    lamp(5.6, "tvalid", s["tvalid"], PRIMARY)
    lamp(7.6, "tlast", s["tlast"], AMBER)

    # cycle counter badge
    box(axL, 7.5, 9.2, 2.2, 0.7, f"cycle {frame}", fc=PRIMARY, ec=PRIMARY,
        fs=10, bold=True, tc="white")

    # ---------- RIGHT: waveforms ----------
    axW.clear()
    axW.set_xlim(0, N)
    axW.set_ylim(0, 9.2)
    axW.axis("off")
    axW.set_title("Digital Waveforms", fontsize=12, fontweight="bold", color=PRIMARY)

    # row labels + baselines
    for name, key, kind in WAVE_ROWS:
        y0 = ROW_Y[name]
        axW.text(-0.2, y0 + 0.35, name, ha="right", va="center", fontsize=9.5,
                 fontweight="bold", color=DK)
        axW.plot([0, N], [y0, y0], color="#eeeeee", lw=0.8, zorder=1)

    # current-cycle sweep line
    axW.axvline(frame + 1, color=ACCENT, lw=1.4, alpha=0.55, zorder=5)
    axW.add_patch(plt.Rectangle((frame, 0), 1, 9.2, color=ACCENT, alpha=0.06, zorder=0))

    # clk: toggles every half handled by drawing square pattern
    clk_vals = [1 if (i % 1) == 0 else 0 for i in range(N)]
    # draw clk as alternating to look like a clock (two ticks per cycle)
    y0 = ROW_Y["clk"]
    for i in range(min(frame + 1, N)):
        # rising in first half, low second half
        axW.plot([i, i + 0.5], [y0 + 0.7, y0 + 0.7], color=DK, lw=2, zorder=3)
        axW.plot([i + 0.5, i + 0.5], [y0, y0 + 0.7], color=DK, lw=2, zorder=3)
        axW.plot([i + 0.5, i + 1], [y0, y0], color=DK, lw=2, zorder=3)
        axW.plot([i + 1, i + 1], [y0, y0 + 0.7], color=DK, lw=2, zorder=3)

    # other rows
    for name, key, kind in WAVE_ROWS:
        if kind == "clk":
            continue
        y0 = ROW_Y[name]
        vals = [r[key] for r in SIG]
        col = {"newd": ACCENT, "tready": GREEN, "tvalid": PRIMARY,
               "tdata": PRIMARY, "tlast": AMBER, "count": AMBER}[name]
        if kind == "bin":
            draw_binary_wave(axW, y0, vals, frame, color=col)
        else:
            draw_bus_wave(axW, y0, vals, frame, color=col)

    # x ticks
    for i in range(0, N + 1, 2):
        axW.text(i, -0.3, str(i), ha="center", fontsize=7, color=GREY)
    axW.text(N / 2, -0.95, "clock cycle", ha="center", fontsize=9, color=DK)

    return []


anim = FuncAnimation(fig, render, frames=N, interval=600, blit=False)
out = OUT / "anim_axis_master.gif"
anim.save(out, writer=PillowWriter(fps=2))
plt.close(fig)
print(f"Saved {out}")
