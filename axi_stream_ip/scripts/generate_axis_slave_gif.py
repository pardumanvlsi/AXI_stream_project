"""Cycle-accurate animated GIF for the AXI4-Stream SLAVE (axis_s).

Each frame = one clock cycle. The figure shows:
  * a live FSM (IDLE / STORE) with the active state highlighted
  * the datapath (incoming tdata -> dout while in STORE)
  * a scrolling digital-waveform pane for clk, tvalid, tlast, tready,
    tdata, dout, state

Stimulus mirrors a master that streams 4 beats (data = 5,10,15,20 here
representing din*count) with tlast on the final beat.

Output: figures/anim_axis_slave.gif
"""
from pathlib import Path
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


# --------------------------------------------------------------------------
# Behavioural model of axis_s
# --------------------------------------------------------------------------
def simulate(n_cycles=22):
    # incoming stream: master asserts tvalid cycles 3..7 with data beats,
    # tlast on the last beat (cycle 7).
    tvalid = [0] * n_cycles
    tlast = [0] * n_cycles
    tdata_in = [0] * n_cycles
    beats = {3: 5, 4: 10, 5: 15, 6: 0, 7: 20}  # cycle 6 = master back-pressure bubble
    for c in range(3, 8):
        if c == 6:
            tvalid[c] = 0  # bubble: no valid this cycle
        else:
            tvalid[c] = 1
            tdata_in[c] = beats[c]
    tlast[7] = 1

    state = "IDLE"
    rows = []
    for c in range(n_cycles):
        tready = 1 if state == "STORE" else 0
        dout = tdata_in[c] if state == "STORE" else 0
        rows.append(dict(cyc=c, tvalid=tvalid[c], tlast=tlast[c],
                         tdata=tdata_in[c], tready=tready, dout=dout, state=state))
        # next state
        nstate = state
        if state == "IDLE":
            if tvalid[c] == 1:
                nstate = "STORE"
        else:  # STORE
            if tlast[c] == 1 and tvalid[c] == 1:
                nstate = "IDLE"
            elif tlast[c] == 0 and tvalid[c] == 1:
                nstate = "STORE"
            else:
                nstate = "IDLE"
        state = nstate
    return rows


SIG = simulate()
N = len(SIG)


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


def draw_binary_wave(ax, y0, values, upto, *, color=DK, height=0.7):
    xs, ys = [], []
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        xs += [i, i + 1]
        ys += [y0 + (height if v else 0)] * 2
        if i > 0:
            ax.plot([i, i], [y0 + (height if values[i - 1] else 0),
                             y0 + (height if v else 0)], color=color, lw=2, zorder=3)
    ax.plot(xs, ys, color=color, lw=2, zorder=3)


def draw_bus_wave(ax, y0, values, upto, *, color=PRIMARY, height=0.7):
    for i in range(min(upto + 1, len(values))):
        v = values[i]
        ax.plot([i, i + 1], [y0 + height, y0 + height], color=color, lw=1.6, zorder=3)
        ax.plot([i, i + 1], [y0, y0], color=color, lw=1.6, zorder=3)
        if i > 0 and values[i] != values[i - 1]:
            ax.plot([i, i], [y0, y0 + height], color=color, lw=1.6, zorder=3)
        ax.text(i + 0.5, y0 + height / 2, str(v), ha="center", va="center",
                fontsize=7.5, color=color, zorder=4)


def draw_state_wave(ax, y0, states, upto, *, height=0.7):
    for i in range(min(upto + 1, len(states))):
        v = states[i]
        col = GREEN if v == "STORE" else GREY
        ax.plot([i, i + 1], [y0 + height, y0 + height], color=col, lw=1.6, zorder=3)
        ax.plot([i, i + 1], [y0, y0], color=col, lw=1.6, zorder=3)
        if i > 0 and states[i] != states[i - 1]:
            ax.plot([i, i], [y0, y0 + height], color=DK, lw=1.6, zorder=3)
        ax.text(i + 0.5, y0 + height / 2, v, ha="center", va="center",
                fontsize=6.5, color=col, zorder=4, fontweight="bold")


fig = plt.figure(figsize=(13, 7.2))
fig.suptitle("AXI4-Stream Slave (axis_s) — Cycle-Accurate Operation",
             fontsize=15, fontweight="bold", color=PRIMARY, y=0.985)

axL = fig.add_axes([0.02, 0.06, 0.40, 0.84])
axW = fig.add_axes([0.46, 0.10, 0.52, 0.78])

WAVE_ROWS = [
    ("clk",    None,     "clk"),
    ("tvalid", "tvalid", "bin"),
    ("tlast",  "tlast",  "bin"),
    ("tready", "tready", "bin"),
    ("tdata",  "tdata",  "bus"),
    ("dout",   "dout",   "bus"),
    ("state",  "state",  "state"),
]
ROW_Y = {name: 8.2 - i * 1.18 for i, (name, _, _) in enumerate(WAVE_ROWS)}


def render(frame):
    s = SIG[frame]
    # ---------- LEFT ----------
    axL.clear()
    axL.set_xlim(0, 10)
    axL.set_ylim(0, 10)
    axL.axis("off")
    axL.text(5.0, 9.6, "FSM  &  Datapath", fontsize=12, fontweight="bold",
             color=PRIMARY, ha="center")

    active = s["state"]
    idle_on = active == "IDLE"
    c1 = Circle((2.6, 7.4), 1.2, facecolor=ACCENT if idle_on else LIGHT,
                edgecolor=ACCENT if idle_on else PRIMARY,
                linewidth=3 if idle_on else 1.8, zorder=3)
    axL.add_patch(c1)
    axL.text(2.6, 7.4, "IDLE", ha="center", va="center", fontsize=12,
             fontweight="bold", color="white" if idle_on else DK, zorder=4)
    store_on = active == "STORE"
    c2 = Circle((7.4, 7.4), 1.2, facecolor=GREEN if store_on else LIGHT3,
                edgecolor=GREEN if store_on else PRIMARY,
                linewidth=3 if store_on else 1.8, zorder=3)
    axL.add_patch(c2)
    axL.text(7.4, 7.4, "STORE", ha="center", va="center", fontsize=11,
             fontweight="bold", color="white" if store_on else DK, zorder=4)

    arrow(axL, 3.8, 7.95, 6.2, 7.95, color=PRIMARY, conn="arc3,rad=-0.3")
    axL.text(5.0, 8.95, "tvalid==1", ha="center", fontsize=8.5, color=PRIMARY,
             fontweight="bold")
    arrow(axL, 6.2, 6.85, 3.8, 6.85, color=PRIMARY, conn="arc3,rad=-0.3")
    axL.text(5.0, 5.95, "tlast & tvalid", ha="center", fontsize=8.5,
             color=PRIMARY, fontweight="bold")

    # datapath
    box(axL, 0.6, 3.4, 2.8, 1.0, f"tdata = {s['tdata']}", fc=PINK, ec=ACCENT,
        fs=11, bold=True)
    box(axL, 4.2, 3.4, 1.2, 1.0, "gate", fc="#f0f0f0" if not store_on else LIGHT3,
        ec=GREEN if store_on else GREY, fs=9, bold=True)
    box(axL, 6.2, 3.4, 2.8, 1.0, f"dout = {s['dout']}",
        fc=LIGHT3 if store_on else "#f0f0f0",
        ec=GREEN if store_on else GREY, fs=11, bold=True)
    arrow(axL, 3.4, 3.9, 4.2, 3.9, color=GREY)
    arrow(axL, 5.4, 3.9, 6.2, 3.9, color=GREEN if store_on else GREY)
    axL.text(5.0, 2.95, "dout = (STORE) ? tdata : 0", ha="center", fontsize=8.5,
             color=DK, style="italic")

    def lamp(x, label, on, on_color):
        c = Circle((x, 1.5), 0.32, facecolor=on_color if on else "#dddddd",
                   edgecolor=DK, linewidth=1.2, zorder=3)
        axL.add_patch(c)
        axL.text(x, 0.75, label, ha="center", fontsize=8.5, color=DK,
                 fontweight="bold")
    lamp(1.6, "tvalid", s["tvalid"], PRIMARY)
    lamp(3.6, "tready", s["tready"], GREEN)
    lamp(5.6, "tlast", s["tlast"], AMBER)
    lamp(7.6, "accept", s["tvalid"] and s["tready"], "#0d7d7d")

    box(axL, 7.5, 9.2, 2.2, 0.7, f"cycle {frame}", fc=PRIMARY, ec=PRIMARY,
        fs=10, bold=True, tc="white")

    # ---------- RIGHT ----------
    axW.clear()
    axW.set_xlim(0, N)
    axW.set_ylim(0, 9.2)
    axW.axis("off")
    axW.set_title("Digital Waveforms", fontsize=12, fontweight="bold", color=PRIMARY)

    for name, key, kind in WAVE_ROWS:
        y0 = ROW_Y[name]
        axW.text(-0.2, y0 + 0.35, name, ha="right", va="center", fontsize=9.5,
                 fontweight="bold", color=DK)
        axW.plot([0, N], [y0, y0], color="#eeeeee", lw=0.8, zorder=1)

    axW.axvline(frame + 1, color=ACCENT, lw=1.4, alpha=0.55, zorder=5)
    axW.add_patch(plt.Rectangle((frame, 0), 1, 9.2, color=ACCENT, alpha=0.06, zorder=0))

    y0 = ROW_Y["clk"]
    for i in range(min(frame + 1, N)):
        axW.plot([i, i + 0.5], [y0 + 0.7, y0 + 0.7], color=DK, lw=2, zorder=3)
        axW.plot([i + 0.5, i + 0.5], [y0, y0 + 0.7], color=DK, lw=2, zorder=3)
        axW.plot([i + 0.5, i + 1], [y0, y0], color=DK, lw=2, zorder=3)
        axW.plot([i + 1, i + 1], [y0, y0 + 0.7], color=DK, lw=2, zorder=3)

    for name, key, kind in WAVE_ROWS:
        if kind == "clk":
            continue
        y0 = ROW_Y[name]
        col = {"tvalid": PRIMARY, "tlast": AMBER, "tready": GREEN,
               "tdata": ACCENT, "dout": GREEN, "state": DK}[name]
        if kind == "bin":
            draw_binary_wave(axW, y0, [r[key] for r in SIG], frame, color=col)
        elif kind == "bus":
            draw_bus_wave(axW, y0, [r[key] for r in SIG], frame, color=col)
        elif kind == "state":
            draw_state_wave(axW, y0, [r[key] for r in SIG], frame)

    for i in range(0, N + 1, 2):
        axW.text(i, -0.3, str(i), ha="center", fontsize=7, color=GREY)
    axW.text(N / 2, -0.95, "clock cycle", ha="center", fontsize=9, color=DK)
    return []


anim = FuncAnimation(fig, render, frames=N, interval=600, blit=False)
out = OUT / "anim_axis_slave.gif"
anim.save(out, writer=PillowWriter(fps=2))
plt.close(fig)
print(f"Saved {out}")
