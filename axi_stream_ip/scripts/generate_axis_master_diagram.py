"""Generate an explanatory diagram for the AXI4-Stream master (axis_m).

Creates a single PPT-ready PNG that shows:
  1. The module's I/O block diagram (clock/reset, input side, AXIS output side)
  2. The 2-state FSM (IDLE / TX) with transitions
  3. The data-beat table showing how tdata = din*count and tlast/tvalid behave

Output: figures/diagram_axis_master.png
"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(exist_ok=True)

PRIMARY = "#1f4e79"
ACCENT = "#c00000"
GREEN = "#2e7d32"
LIGHT = "#deebf7"
LIGHT2 = "#fff2cc"
LIGHT3 = "#e2efda"
PINK = "#fce4d6"
GREY = "#595959"


def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=1.6, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", color=tc)


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=1.8, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=16, linewidth=lw, color=color)
    ax.add_patch(a)


def main():
    fig = plt.figure(figsize=(14, 8.5))
    fig.suptitle("AXI4-Stream Master (axis_m) — Operation Overview",
                 fontsize=16, fontweight="bold", color=PRIMARY, y=0.98)

    # =====================================================================
    # Panel A : I/O Block diagram (top-left)
    # =====================================================================
    axA = fig.add_axes([0.03, 0.50, 0.45, 0.42])
    axA.set_xlim(0, 10)
    axA.set_ylim(0, 8)
    axA.axis("off")
    axA.set_title("(a)  Module I/O & Datapath", fontsize=12, fontweight="bold")

    # central module
    box(axA, 3.2, 1.4, 3.6, 5.0, "", fc="#f7f9fc", ec=PRIMARY)
    axA.text(5.0, 5.9, "axis_m", fontsize=13, fontweight="bold", color=PRIMARY,
             ha="center")
    box(axA, 3.5, 3.6, 3.0, 1.0, "FSM\nIDLE / TX", fc=LIGHT, ec=PRIMARY, fs=10, bold=True)
    box(axA, 3.5, 2.2, 3.0, 0.9, "count\n(0 \u2192 3)", fc=LIGHT2, ec=PRIMARY, fs=9, bold=True)

    # left-side inputs
    inputs = [
        ("m_axis_aclk", 6.3),
        ("m_axis_aresetn", 5.6),
        ("newd", 4.6),
        ("din[7:0]", 3.6),
    ]
    for name, y in inputs:
        box(axA, 0.2, y - 0.28, 2.4, 0.56, name, fc=PINK, ec=ACCENT, fs=9)
        arrow(axA, 2.6, y, 3.2, y, color=ACCENT)

    # handshake input from slave (tready returns)
    box(axA, 0.2, 1.9, 2.4, 0.56, "m_axis_tready", fc=LIGHT3, ec=GREEN, fs=9)
    arrow(axA, 2.6, 2.18, 3.2, 2.18, color=GREEN)

    # right-side AXIS outputs
    outputs = [
        ("m_axis_tvalid", 5.6),
        ("m_axis_tdata[7:0]", 4.6),
        ("m_axis_tlast", 3.6),
    ]
    for name, y in outputs:
        box(axA, 7.4, y - 0.28, 2.4, 0.56, name, fc=LIGHT3, ec=GREEN, fs=9)
        arrow(axA, 6.8, y, 7.4, y, color=GREEN)

    axA.text(8.6, 6.6, "AXI4-Stream\nmaster port", fontsize=9, color=GREEN,
             ha="center", fontweight="bold")
    axA.text(1.4, 7.0, "control / data\ninputs", fontsize=9, color=ACCENT,
             ha="center", fontweight="bold")

    # =====================================================================
    # Panel B : FSM (top-right)
    # =====================================================================
    axB = fig.add_axes([0.52, 0.50, 0.45, 0.42])
    axB.set_xlim(0, 10)
    axB.set_ylim(0, 8)
    axB.axis("off")
    axB.set_title("(b)  Finite State Machine", fontsize=12, fontweight="bold")

    # IDLE state
    c1 = Circle((2.6, 4.0), 1.25, facecolor=LIGHT, edgecolor=PRIMARY, linewidth=2)
    axB.add_patch(c1)
    axB.text(2.6, 4.0, "IDLE", ha="center", va="center", fontsize=12, fontweight="bold")
    # TX state
    c2 = Circle((7.4, 4.0), 1.25, facecolor=LIGHT3, edgecolor=GREEN, linewidth=2)
    axB.add_patch(c2)
    axB.text(7.4, 4.0, "TX", ha="center", va="center", fontsize=12, fontweight="bold")

    # reset entry
    arrow(axB, 2.6, 7.2, 2.6, 5.25, color=ACCENT)
    axB.text(2.6, 7.45, "reset", ha="center", fontsize=9, color=ACCENT, fontweight="bold")

    # IDLE -> TX
    arrow(axB, 3.85, 4.55, 6.15, 4.55, color=PRIMARY, conn="arc3,rad=-0.25")
    axB.text(5.0, 5.6, "newd == 1", ha="center", fontsize=9.5, color=PRIMARY,
             fontweight="bold")

    # TX -> IDLE
    arrow(axB, 6.15, 3.45, 3.85, 3.45, color=PRIMARY, conn="arc3,rad=-0.25")
    axB.text(5.0, 2.35, "tready==1 &&\ncount == 3", ha="center", fontsize=9.5,
             color=PRIMARY, fontweight="bold")

    # TX self loop (streaming beats)
    arrow(axB, 8.35, 4.7, 8.35, 3.3, color=GREEN, conn="arc3,rad=-1.6")
    axB.text(9.55, 4.0, "stream\nbeat\n(count++)", ha="center", fontsize=8.5,
             color=GREEN, fontweight="bold")

    # IDLE self loop (waiting)
    arrow(axB, 1.65, 3.3, 1.65, 4.7, color=GREY, conn="arc3,rad=-1.6")
    axB.text(0.45, 4.0, "newd==0\n(wait)", ha="center", fontsize=8.5, color=GREY)

    # =====================================================================
    # Panel C : Beat table (bottom-left)
    # =====================================================================
    axC = fig.add_axes([0.04, 0.05, 0.60, 0.36])
    axC.set_xlim(0, 11)
    axC.set_ylim(0, 6)
    axC.axis("off")
    axC.set_title("(c)  Transaction Timeline  —  4 beats per 'newd' pulse",
                  fontsize=12, fontweight="bold")

    headers = ["state", "count", "tvalid", "tdata", "tlast", "comment"]
    rows = [
        ["IDLE", "0", "0", "0",        "0", "wait for newd"],
        ["TX",   "0", "1", "din\u00d70", "0", "beat 0"],
        ["TX",   "1", "1", "din\u00d71", "0", "beat 1"],
        ["TX",   "2", "1", "din\u00d72", "0", "beat 2"],
        ["TX",   "3", "1", "din\u00d73", "1", "LAST \u2192 IDLE"],
    ]
    col_x = [0.15, 1.75, 3.20, 4.75, 6.55, 8.05]
    col_w = [1.60, 1.45, 1.55, 1.80, 1.50, 2.80]

    # header row
    for x, w, h in zip(col_x, col_w, headers):
        box(axC, x, 4.9, w - 0.12, 0.9, h, fc=PRIMARY, ec=PRIMARY, fs=10,
            bold=True, tc="white")

    for r, row in enumerate(rows):
        y = 4.9 - (r + 1) * 0.92
        for c, (x, w, val) in enumerate(zip(col_x, col_w, row)):
            if row[0] == "IDLE":
                fc = "#f2f2f2"
            elif val == "1" and headers[c] == "tlast":
                fc = LIGHT2
            else:
                fc = LIGHT3 if c == 0 else "white"
            box(axC, x, y, w - 0.12, 0.82, val, fc=fc, ec=GREY, fs=9.5,
                bold=(headers[c] == "tlast" and val == "1"))

    # =====================================================================
    # Panel D : Key equations (bottom-right)
    # =====================================================================
    axD = fig.add_axes([0.66, 0.05, 0.31, 0.36])
    axD.set_xlim(0, 10)
    axD.set_ylim(0, 6)
    axD.axis("off")
    axD.set_title("(d)  Key Assignments", fontsize=12, fontweight="bold")
    eqs = ("tvalid = (state == TX)\n\n"
           "tdata  = tvalid ? din \u00d7 count : 0\n\n"
           "tlast  = (count == 3 && state == TX)\n\n"
           "count++  only when\n"
           "(TX && tready && count != 3)")
    p = FancyBboxPatch((0.3, 0.3), 9.4, 5.2,
                       boxstyle="round,pad=0.02,rounding_size=0.06",
                       linewidth=1.6, edgecolor=ACCENT, facecolor="#fdf6e3")
    axD.add_patch(p)
    axD.text(0.7, 2.9, eqs, ha="left", va="center", fontsize=11,
             family="monospace", color="#333333")

    out = OUT / "diagram_axis_master.png"
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
