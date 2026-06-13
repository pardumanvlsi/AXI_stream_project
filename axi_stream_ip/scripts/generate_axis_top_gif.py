"""Cycle-accurate animated GIF for the AXI4-Stream TOP integration (top).

Animates the MASTER and SLAVE FSMs simultaneously, the AXIS handshake
channel between them (tdata/tvalid/tlast forward, tready back), an animated
data token crossing the channel on each accepted beat, and a combined
waveform strip.

The single behavioural model below instantiates both axis_m and axis_s and
connects them exactly as in `top` (ready_t, valid_t, data, last_t).

Output: figures/anim_axis_top.gif
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
PURPLE = "#6a1b9a"
LIGHT = "#deebf7"
LIGHT3 = "#e2efda"
PINK = "#fce4d6"
GREY = "#888888"
DK = "#222222"
DIN_VAL = 5


# --------------------------------------------------------------------------
# Combined behavioural model: master + slave wired as `top`
# --------------------------------------------------------------------------
def simulate(n_cycles=20):
    newd = [0] * n_cycles
    newd[2] = 1

    m_state, count = "IDLE", 0
    s_state = "IDLE"
    rows = []
    for c in range(n_cycles):
        # ---- master combinational outputs ----
        valid_t = 1 if m_state == "TX" else 0
        data = (DIN_VAL * count) if valid_t else 0
        last_t = 1 if (count == 3 and m_state == "TX") else 0
        # ---- slave combinational output (ready) depends on slave state ----
        ready_t = 1 if s_state == "STORE" else 0
        dout = data if s_state == "STORE" else 0
        accept = valid_t and ready_t

        rows.append(dict(cyc=c, newd=newd[c], m_state=m_state, count=count,
                         valid_t=valid_t, data=data, last_t=last_t,
                         ready_t=ready_t, s_state=s_state, dout=dout,
                         accept=accept))

        # ---- master next-state ----
        nm, ncount = m_state, count
        if m_state == "IDLE":
            ncount = 0
            if newd[c] == 1:
                nm = "TX"
        else:
            if ready_t == 1:
                if count != 3:
                    ncount = count + 1
                    nm = "TX"
                else:
                    nm = "IDLE"
            else:
                nm = "TX"
        # ---- slave next-state ----
        ns = s_state
        if s_state == "IDLE":
            if valid_t == 1:
                ns = "STORE"
        else:
            if last_t == 1 and valid_t == 1:
                ns = "IDLE"
            elif last_t == 0 and valid_t == 1:
                ns = "STORE"
            else:
                ns = "IDLE"
        m_state, count, s_state = nm, ncount, ns
    return rows


SIG = simulate()
N = len(SIG)


def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=4)
    return p


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=2.0, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=16, linewidth=lw, color=color, zorder=2)
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
                fontsize=7, color=color, zorder=4)


fig = plt.figure(figsize=(13.5, 7.6))
fig.suptitle("AXI4-Stream Top (top) — Master \u2192 Slave Handshake (Cycle-Accurate)",
             fontsize=15, fontweight="bold", color=PRIMARY, y=0.985)

axT = fig.add_axes([0.02, 0.40, 0.96, 0.50])  # block/handshake area
axW = fig.add_axes([0.08, 0.06, 0.86, 0.28])  # waveform strip

WAVE_ROWS = [
    ("clk",    None,      "clk"),
    ("newd",   "newd",    "bin"),
    ("valid",  "valid_t", "bin"),
    ("ready",  "ready_t", "bin"),
    ("data",   "data",    "bus"),
    ("last",   "last_t",  "bin"),
    ("dout",   "dout",    "bus"),
]
ROW_Y = {name: 5.0 - i * 0.78 for i, (name, _, _) in enumerate(WAVE_ROWS)}


def render(frame):
    s = SIG[frame]

    # =================== TOP: blocks + handshake ===================
    axT.clear()
    axT.set_xlim(0, 16)
    axT.set_ylim(0, 9)
    axT.axis("off")

    # cycle badge
    box(axT, 13.4, 8.0, 2.2, 0.8, f"cycle {frame}", fc=PRIMARY, ec=PRIMARY,
        fs=11, bold=True, tc="white")

    # ---- MASTER block ----
    m_tx = s["m_state"] == "TX"
    box(axT, 1.2, 2.6, 4.2, 4.6, "", fc=LIGHT, ec=PRIMARY)
    axT.text(3.3, 6.85, "axis_m  (MASTER)", fontsize=12, fontweight="bold",
             color=PRIMARY, ha="center")
    # master state pill
    box(axT, 2.0, 5.4, 2.6, 0.9,
        f"state: {s['m_state']}",
        fc=GREEN if m_tx else "#ffffff", ec=GREEN if m_tx else PRIMARY,
        fs=10, bold=True, tc="white" if m_tx else DK)
    box(axT, 2.0, 4.2, 2.6, 0.8, f"count = {s['count']}", fc="#fff2cc",
        ec=AMBER, fs=10, bold=True)
    box(axT, 2.0, 3.1, 2.6, 0.8, f"tdata = {s['data']}",
        fc=LIGHT3 if s["valid_t"] else "#f0f0f0",
        ec=GREEN if s["valid_t"] else GREY, fs=10, bold=True)

    # ---- SLAVE block ----
    s_store = s["s_state"] == "STORE"
    box(axT, 10.6, 2.6, 4.2, 4.6, "", fc=LIGHT3, ec=GREEN)
    axT.text(12.7, 6.85, "axis_s  (SLAVE)", fontsize=12, fontweight="bold",
             color=GREEN, ha="center")
    box(axT, 11.4, 5.4, 2.6, 0.9, f"state: {s['s_state']}",
        fc=GREEN if s_store else "#ffffff", ec=GREEN if s_store else PRIMARY,
        fs=10, bold=True, tc="white" if s_store else DK)
    box(axT, 11.4, 3.1, 2.6, 0.8, f"dout = {s['dout']}",
        fc=LIGHT3 if s_store else "#f0f0f0",
        ec=GREEN if s_store else GREY, fs=10, bold=True)

    # ---- AXIS channel arrows ----
    # data (purple), valid (red), last (amber) forward ; ready (green) back
    arrow(axT, 5.4, 5.6, 10.6, 5.6, color=PURPLE, lw=2.6)
    axT.text(8.0, 5.95, f"data = {s['data']}  (tdata)", ha="center", fontsize=9.5,
             color=PURPLE, fontweight="bold")
    arrow(axT, 5.4, 4.8, 10.6, 4.8,
          color=ACCENT if s["valid_t"] else "#e3bcbc", lw=2.4)
    axT.text(8.0, 4.55, f"valid_t = {s['valid_t']}", ha="center", fontsize=9,
             color=ACCENT, fontweight="bold")
    arrow(axT, 5.4, 4.0, 10.6, 4.0,
          color=AMBER if s["last_t"] else "#e6d4a6", lw=2.4)
    axT.text(8.0, 3.75, f"last_t = {s['last_t']}", ha="center", fontsize=9,
             color=AMBER, fontweight="bold")
    arrow(axT, 10.6, 3.2, 5.4, 3.2,
          color=GREEN if s["ready_t"] else "#bcd6bc", lw=2.4)
    axT.text(8.0, 2.85, f"ready_t = {s['ready_t']}", ha="center", fontsize=9,
             color=GREEN, fontweight="bold")

    # ---- animated data token on accepted beat ----
    if s["accept"]:
        tx_pos = 8.0
        tok = Circle((tx_pos, 5.6), 0.42, facecolor=PURPLE, edgecolor="white",
                     linewidth=1.5, zorder=6)
        axT.add_patch(tok)
        axT.text(tx_pos, 5.6, str(s["data"]), ha="center", va="center",
                 fontsize=9, color="white", fontweight="bold", zorder=7)
        axT.text(8.0, 6.55, "BEAT ACCEPTED", ha="center", fontsize=9,
                 color="#0d7d7d", fontweight="bold")

    # ---- top-level ports ----
    box(axT, 0.1, 6.0, 1.0, 0.6, "newd", fc=PINK, ec=ACCENT, fs=8)
    arrow(axT, 1.1, 6.3, 1.2, 5.85, color=ACCENT, lw=1.6)
    box(axT, 0.1, 4.6, 1.0, 0.6, "din=5", fc=PINK, ec=ACCENT, fs=8)
    arrow(axT, 1.1, 4.9, 1.2, 4.6, color=ACCENT, lw=1.6)
    box(axT, 14.9, 3.2, 1.0, 0.6, "dout", fc=LIGHT3, ec=GREEN, fs=8)
    arrow(axT, 14.8, 3.5, 14.9, 3.5, color=GREEN, lw=1.6)
    box(axT, 14.9, 4.0, 1.0, 0.6, "last", fc="#fff2cc", ec=AMBER, fs=8)

    # =================== BOTTOM: waveform strip ===================
    axW.clear()
    axW.set_xlim(0, N)
    axW.set_ylim(-0.6, 5.7)
    axW.axis("off")
    axW.text(N / 2, 5.5, "Combined Waveforms", ha="center", fontsize=11,
             fontweight="bold", color=PRIMARY)

    for name, key, kind in WAVE_ROWS:
        y0 = ROW_Y[name]
        axW.text(-0.15, y0 + 0.3, name, ha="right", va="center", fontsize=8.5,
                 fontweight="bold", color=DK)
        axW.plot([0, N], [y0, y0], color="#eeeeee", lw=0.7, zorder=1)

    axW.axvline(frame + 1, color=ACCENT, lw=1.3, alpha=0.5, zorder=5)
    axW.add_patch(plt.Rectangle((frame, -0.6), 1, 6.3, color=ACCENT, alpha=0.06,
                                zorder=0))

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
        col = {"newd": ACCENT, "valid": ACCENT, "ready": GREEN,
               "data": PURPLE, "last": AMBER, "dout": GREEN}[name]
        if kind == "bin":
            draw_binary_wave(axW, y0, [r[key] for r in SIG], frame, color=col)
        else:
            draw_bus_wave(axW, y0, [r[key] for r in SIG], frame, color=col)

    for i in range(0, N + 1, 2):
        axW.text(i, -0.45, str(i), ha="center", fontsize=6.5, color=GREY)
    return []


anim = FuncAnimation(fig, render, frames=N, interval=650, blit=False)
out = OUT / "anim_axis_top.gif"
anim.save(out, writer=PillowWriter(fps=2))
plt.close(fig)
print(f"Saved {out}")
