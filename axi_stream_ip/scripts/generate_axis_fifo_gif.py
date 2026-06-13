"""Cycle-accurate animated GIF for the AXI4-Stream FIFO (axis_fifo).

Each frame = one clock cycle. The figure shows:
  * the 16-slot circular buffer with live fill state, moving wr_ptr / rd_ptr,
    and the data value held in each occupied slot
  * occupancy gauge (count) with full / empty lamps
  * a scrolling waveform pane: clk, s_tvalid, s_tdata, wr, m_tready,
    m_tvalid, m_tdata, count

The behavioural model reproduces the RTL exactly: on each clock only ONE of
reset / write(tvalid & !full) / read(tready & !empty) occurs (write priority).

Output: figures/anim_axis_fifo.gif
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge, Circle, Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(exist_ok=True)

PRIMARY = "#1f4e79"
ACCENT = "#c00000"
GREEN = "#2e7d32"
AMBER = "#b8860b"
PURPLE = "#6a1b9a"
LIGHT = "#deebf7"
LIGHT2 = "#fff2cc"
LIGHT3 = "#e2efda"
PINK = "#fce4d6"
GREY = "#888888"
DK = "#222222"

DEPTH = 16
FULL_CNT = 15  # RTL: full when count == 15


# --------------------------------------------------------------------------
# Behavioural model of axis_fifo
# --------------------------------------------------------------------------
def simulate():
    # Stimulus: a burst of writes first (fill), then reads drain it, with a
    # couple of overlapping-request cycles to show write-priority.
    # Each entry: (s_tvalid, s_tdata, m_tready)
    stim = []
    # write 6 beats (data 10,20,...60)
    for k in range(6):
        stim.append((1, (k + 1) * 10, 0))
    # idle 1
    stim.append((0, 0, 0))
    # overlapping write+read request (write wins) while also writing
    stim.append((1, 70, 1))
    stim.append((1, 80, 1))
    # now only reads
    for _ in range(8):
        stim.append((0, 0, 1))
    # trailing idle
    stim.append((0, 0, 0))
    stim.append((0, 0, 0))

    mem = [None] * DEPTH
    wr = rd = count = 0
    m_tvalid = 0
    m_tdata = 0
    rows = []
    for (s_tvalid, s_tdata, m_tready) in stim:
        full = 1 if count == FULL_CNT else 0
        empty = 1 if count == 0 else 0

        do_write = (s_tvalid == 1 and full == 0)
        do_read = (not do_write) and (m_tready == 1 and empty == 0)

        # snapshot BEFORE the edge effects for display of this cycle
        rows.append(dict(
            s_tvalid=s_tvalid, s_tdata=s_tdata, m_tready=m_tready,
            full=full, empty=empty, count=count,
            wr=wr % DEPTH, rd=rd % DEPTH,
            mem=list(mem), do_write=do_write, do_read=do_read,
            m_tvalid=m_tvalid, m_tdata=m_tdata,
        ))

        # ---- registered updates (next state) ----
        if do_write:
            mem[wr % DEPTH] = s_tdata
            wr = (wr + 1) % DEPTH
            count += 1
            m_tvalid = 0
            m_tdata = 0
        elif do_read:
            m_tdata = mem[rd % DEPTH]
            m_tvalid = 1
            rd = (rd + 1) % DEPTH
            count -= 1
    return rows


SIG = simulate()
N = len(SIG)


def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=4)


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=1.8, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=14, linewidth=lw, color=color, zorder=5)
    ax.add_patch(a)


def draw_binary_wave(ax, y0, values, upto, *, color=DK, height=0.6):
    xs, ys = [], []
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        xs += [i, i + 1]
        ys += [y0 + (height if v else 0)] * 2
        if i > 0:
            ax.plot([i, i], [y0 + (height if values[i - 1] else 0),
                             y0 + (height if v else 0)], color=color, lw=2, zorder=3)
    ax.plot(xs, ys, color=color, lw=2, zorder=3)


def draw_bus_wave(ax, y0, values, upto, *, color=PRIMARY, height=0.6):
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        ax.plot([i, i + 1], [y0 + height, y0 + height], color=color, lw=1.5, zorder=3)
        ax.plot([i, i + 1], [y0, y0], color=color, lw=1.5, zorder=3)
        if i > 0 and values[i] != values[i - 1]:
            ax.plot([i, i], [y0, y0 + height], color=color, lw=1.5, zorder=3)
        ax.text(i + 0.5, y0 + height / 2, str(v), ha="center", va="center",
                fontsize=6.8, color=color, zorder=4)


fig = plt.figure(figsize=(13.5, 7.6))
fig.suptitle("AXI4-Stream FIFO (axis_fifo) — Cycle-Accurate Operation",
             fontsize=15, fontweight="bold", color=PRIMARY, y=0.985)

axR = fig.add_axes([0.02, 0.05, 0.42, 0.85])   # ring + gauges
axW = fig.add_axes([0.49, 0.10, 0.49, 0.78])   # waveforms

WAVE_ROWS = [
    ("clk",      None,       "clk"),
    ("s_tvalid", "s_tvalid", "bin"),
    ("s_tdata",  "s_tdata",  "bus"),
    ("wr",       "do_write", "bin"),
    ("m_tready", "m_tready", "bin"),
    ("m_tvalid", "m_tvalid", "bin"),
    ("m_tdata",  "m_tdata",  "bus"),
    ("count",    "count",    "bus"),
]
ROW_Y = {name: 9.0 - i * 1.05 for i, (name, _, _) in enumerate(WAVE_ROWS)}


def render(frame):
    s = SIG[frame]

    # ================= LEFT: ring + gauges =================
    axR.clear()
    axR.set_xlim(-1.8, 1.8)
    axR.set_ylim(-2.5, 2.2)
    axR.axis("off")
    axR.set_title("Circular Buffer (16 slots)", fontsize=12, fontweight="bold",
                  color=PRIMARY, pad=2)

    r_out, r_in = 1.55, 1.0
    mem = s["mem"]
    for i in range(DEPTH):
        a0 = 90 - i * 360 / DEPTH
        a1 = 90 - (i + 1) * 360 / DEPTH
        occupied = mem[i] is not None
        # highlight slot being written / read this cycle
        if s["do_write"] and i == s["wr"]:
            fc, ec, lw = "#ffe08a", ACCENT, 2.4
        elif s["do_read"] and i == s["rd"]:
            fc, ec, lw = "#a5d6a7", GREEN, 2.4
        else:
            fc, ec, lw = (LIGHT3 if occupied else "white"), PRIMARY, 1.1
        w = Wedge((0, 0), r_out, a1, a0, width=r_out - r_in,
                  facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2)
        axR.add_patch(w)
        am = np.deg2rad((a0 + a1) / 2)
        rm = (r_out + r_in) / 2
        label = str(mem[i]) if occupied else str(i)
        axR.text(rm * np.cos(am), rm * np.sin(am), label, ha="center",
                 va="center", fontsize=7.5 if occupied else 6.5,
                 color=DK if occupied else GREY,
                 fontweight="bold" if occupied else "normal", zorder=3)

    axR.text(0, 0.05, "mem_d /", ha="center", fontsize=8.5, color=PRIMARY,
             fontweight="bold")
    axR.text(0, -0.25, "mem_k / mem_l", ha="center", fontsize=7.5, color=GREY)

    def ptr(idx, label, color, rad=1.78):
        a = np.deg2rad(90 - (idx + 0.5) * 360 / DEPTH)
        x0, y0 = rad * np.cos(a), rad * np.sin(a)
        x1, y1 = (r_out + 0.02) * np.cos(a), (r_out + 0.02) * np.sin(a)
        arrow(axR, x0, y0, x1, y1, color=color, lw=2.2)
        axR.text((rad + 0.18) * np.cos(a), (rad + 0.18) * np.sin(a), label,
                 ha="center", va="center", fontsize=8, color=color,
                 fontweight="bold")
    ptr(s["wr"], "wr", ACCENT)
    ptr(s["rd"], "rd", GREEN)

    # occupancy gauge bar
    gx, gy, gw, gh = -1.5, -2.35, 3.0, 0.34
    axR.add_patch(Rectangle((gx, gy), gw, gh, facecolor="white",
                            edgecolor=DK, linewidth=1.2, zorder=2))
    frac = s["count"] / DEPTH
    axR.add_patch(Rectangle((gx, gy), gw * frac, gh,
                            facecolor=AMBER, edgecolor="none", zorder=2))
    axR.text(0, gy + gh / 2, f"count = {s['count']} / {DEPTH}", ha="center",
             va="center", fontsize=8.5, color=DK, fontweight="bold", zorder=4)

    # action + flag lamps
    def lamp(x, y, label, on, on_color):
        c = Circle((x, y), 0.13, facecolor=on_color if on else "#dddddd",
                   edgecolor=DK, linewidth=1.0, zorder=4)
        axR.add_patch(c)
        axR.text(x + 0.22, y, label, ha="left", va="center", fontsize=8,
                 color=DK, fontweight="bold")
    lamp(-1.5, -1.75, "WRITE", s["do_write"], ACCENT)
    lamp(-0.2, -1.75, "READ", s["do_read"], GREEN)
    lamp(-1.5, -2.02, "full", s["full"], "#c0392b")
    lamp(-0.2, -2.02, "empty", s["empty"], "#7f8c8d")

    # cycle badge
    box(axR, 0.9, 1.85, 0.85, 0.32, f"cyc {frame}", fc=PRIMARY, ec=PRIMARY,
        fs=8.5, bold=True, tc="white")

    # ================= RIGHT: waveforms =================
    axW.clear()
    axW.set_xlim(0, N)
    axW.set_ylim(0, 9.8)
    axW.axis("off")
    axW.set_title("Digital Waveforms", fontsize=12, fontweight="bold",
                  color=PRIMARY)

    for name, key, kind in WAVE_ROWS:
        y0 = ROW_Y[name]
        axW.text(-0.2, y0 + 0.3, name, ha="right", va="center", fontsize=8.5,
                 fontweight="bold", color=DK)
        axW.plot([0, N], [y0, y0], color="#eeeeee", lw=0.7, zorder=1)

    axW.axvline(frame + 1, color=ACCENT, lw=1.3, alpha=0.5, zorder=5)
    axW.add_patch(Rectangle((frame, 0), 1, 9.8, color=ACCENT, alpha=0.06, zorder=0))

    y0 = ROW_Y["clk"]
    for i in range(min(frame + 1, N)):
        axW.plot([i, i + 0.5], [y0 + 0.6, y0 + 0.6], color=DK, lw=1.8, zorder=3)
        axW.plot([i + 0.5, i + 0.5], [y0, y0 + 0.6], color=DK, lw=1.8, zorder=3)
        axW.plot([i + 0.5, i + 1], [y0, y0], color=DK, lw=1.8, zorder=3)
        axW.plot([i + 1, i + 1], [y0, y0 + 0.6], color=DK, lw=1.8, zorder=3)

    for name, key, kind in WAVE_ROWS:
        if kind == "clk":
            continue
        y0 = ROW_Y[name]
        col = {"s_tvalid": ACCENT, "s_tdata": ACCENT, "wr": PURPLE,
               "m_tready": GREEN, "m_tvalid": PRIMARY, "m_tdata": GREEN,
               "count": AMBER}[name]
        if kind == "bin":
            draw_binary_wave(axW, y0, [r[key] for r in SIG], frame, color=col)
        else:
            draw_bus_wave(axW, y0, [r[key] for r in SIG], frame, color=col)

    for i in range(0, N + 1, 2):
        axW.text(i, -0.35, str(i), ha="center", fontsize=6.5, color=GREY)
    axW.text(N / 2, -0.95, "clock cycle", ha="center", fontsize=9, color=DK)
    return []


anim = FuncAnimation(fig, render, frames=N, interval=650, blit=False)
out = OUT / "anim_axis_fifo.gif"
anim.save(out, writer=PillowWriter(fps=2))
plt.close(fig)
print(f"Saved {out}")
