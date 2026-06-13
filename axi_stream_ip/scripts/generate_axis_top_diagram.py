"""Generate an explanatory diagram for the AXI4-Stream top integration (top).

Shows the master (axis_m) and slave (axis_s) connected through the AXIS
handshake channel, the port mapping, and the signal-direction legend.

Output: figures/diagram_axis_top.png
"""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent.parent / "figures"
OUT.mkdir(exist_ok=True)

PRIMARY = "#1f4e79"
ACCENT = "#c00000"
GREEN = "#2e7d32"
PURPLE = "#6a1b9a"
LIGHT = "#deebf7"
LIGHT2 = "#fff2cc"
LIGHT3 = "#e2efda"
PINK = "#fce4d6"
GREY = "#595959"


def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.8, edgecolor=ec, facecolor=fc)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", color=tc)


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=2.0, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=16, linewidth=lw, color=color)
    ax.add_patch(a)


def main():
    fig = plt.figure(figsize=(14, 8.5))
    fig.suptitle("AXI4-Stream Top Integration (top) — Master \u2192 Slave Handshake",
                 fontsize=16, fontweight="bold", color=PRIMARY, y=0.98)

    # =====================================================================
    # Panel A : Connection block diagram (top, full width)
    # =====================================================================
    axA = fig.add_axes([0.03, 0.40, 0.94, 0.50])
    axA.set_xlim(0, 16)
    axA.set_ylim(0, 9)
    axA.axis("off")

    # top-level wrapper outline
    box(axA, 0.3, 0.4, 15.4, 8.0, "", fc="#f9fbfd", ec=PRIMARY)
    axA.text(8.0, 8.05, "top", fontsize=13, fontweight="bold", color=PRIMARY, ha="center")

    # Master block
    box(axA, 3.0, 2.2, 3.6, 4.4, "", fc=LIGHT, ec=PRIMARY)
    axA.text(4.8, 6.15, "axis_m  (m1)", fontsize=12, fontweight="bold",
             color=PRIMARY, ha="center")
    axA.text(4.8, 5.55, "MASTER", fontsize=9.5, color=PRIMARY, ha="center")

    # Slave block
    box(axA, 9.4, 2.2, 3.6, 4.4, "", fc=LIGHT3, ec=GREEN)
    axA.text(11.2, 6.15, "axis_s  (s1)", fontsize=12, fontweight="bold",
             color=GREEN, ha="center")
    axA.text(11.2, 5.55, "SLAVE", fontsize=9.5, color=GREEN, ha="center")

    # ---- AXIS channel between them ----
    # tdata  (M -> S)
    arrow(axA, 6.6, 5.0, 9.4, 5.0, color=PURPLE, lw=2.4)
    axA.text(8.0, 5.35, "data[7:0]", ha="center", fontsize=10, color=PURPLE,
             fontweight="bold")
    axA.text(8.0, 4.7, "(tdata)", ha="center", fontsize=8, color=PURPLE)

    # tvalid (M -> S)
    arrow(axA, 6.6, 4.2, 9.4, 4.2, color=ACCENT, lw=2.2)
    axA.text(8.0, 4.0, "valid_t (tvalid)", ha="center", fontsize=9.5, color=ACCENT,
             fontweight="bold")

    # tlast  (M -> S)
    arrow(axA, 6.6, 3.4, 9.4, 3.4, color="#b8860b", lw=2.2)
    axA.text(8.0, 3.2, "last_t (tlast)", ha="center", fontsize=9.5, color="#b8860b",
             fontweight="bold")

    # tready (S -> M)  -- reverse direction
    arrow(axA, 9.4, 2.7, 6.6, 2.7, color=GREEN, lw=2.2)
    axA.text(8.0, 2.45, "ready_t (tready)", ha="center", fontsize=9.5, color=GREEN,
             fontweight="bold")

    # ---- top-level primary inputs into master ----
    box(axA, 0.6, 5.6, 1.8, 0.7, "newd", fc=PINK, ec=ACCENT, fs=9)
    arrow(axA, 2.4, 5.95, 3.0, 5.95, color=ACCENT)
    box(axA, 0.6, 4.6, 1.8, 0.7, "din[7:0]", fc=PINK, ec=ACCENT, fs=9)
    arrow(axA, 2.4, 4.95, 3.0, 4.95, color=ACCENT)
    box(axA, 0.6, 3.0, 1.8, 0.7, "clk / rst", fc="#ededed", ec=GREY, fs=9)
    arrow(axA, 2.4, 3.35, 3.0, 3.35, color=GREY)

    # ---- top-level outputs from slave ----
    box(axA, 13.6, 4.6, 1.8, 0.7, "dout[7:0]", fc=LIGHT3, ec=GREEN, fs=9)
    arrow(axA, 13.0, 4.95, 13.6, 4.95, color=GREEN)
    # last output tapped from last_t
    box(axA, 13.6, 3.3, 1.8, 0.7, "last", fc=LIGHT2, ec="#b8860b", fs=9)
    arrow(axA, 8.0, 3.4, 8.0, 1.2, color="#b8860b", lw=1.6, conn="arc3,rad=0")
    arrow(axA, 8.0, 1.2, 14.5, 1.2, color="#b8860b", lw=1.6)
    arrow(axA, 14.5, 1.2, 14.5, 3.3, color="#b8860b", lw=1.6)
    axA.text(11.0, 1.0, "assign last = last_t", ha="center", fontsize=8.5,
             color="#b8860b", style="italic")

    # =====================================================================
    # Panel B : Port-mapping table (bottom-left)
    # =====================================================================
    axB = fig.add_axes([0.04, 0.04, 0.56, 0.30])
    axB.set_xlim(0, 12)
    axB.set_ylim(0, 6)
    axB.axis("off")
    axB.set_title("Signal Connections (internal wires)", fontsize=11.5,
                  fontweight="bold")

    headers = ["wire", "driven by (master)", "used by (slave)", "dir"]
    rows = [
        ["data[7:0]", "m_axis_tdata",  "s_axis_tdata",  "M \u2192 S"],
        ["valid_t",   "m_axis_tvalid", "s_axis_tvalid", "M \u2192 S"],
        ["last_t",    "m_axis_tlast",  "s_axis_tlast",  "M \u2192 S"],
        ["ready_t",   "m_axis_tready", "s_axis_tready", "S \u2192 M"],
    ]
    col_x = [0.15, 2.55, 6.10, 9.65]
    col_w = [2.40, 3.55, 3.55, 2.25]
    for x, w, h in zip(col_x, col_w, headers):
        box(axB, x, 4.7, w - 0.12, 0.9, h, fc=PRIMARY, ec=PRIMARY, fs=9.5,
            bold=True, tc="white")
    for r, row in enumerate(rows):
        y = 4.7 - (r + 1) * 0.95
        for c, (x, w, val) in enumerate(zip(col_x, col_w, row)):
            fc = LIGHT3 if "S \u2192 M" in row[3] else "white"
            box(axB, x, y, w - 0.12, 0.85, val, fc=fc, ec=GREY, fs=9)

    # =====================================================================
    # Panel C : Data-flow summary (bottom-right)
    # =====================================================================
    axC = fig.add_axes([0.63, 0.04, 0.34, 0.30])
    axC.set_xlim(0, 10)
    axC.set_ylim(0, 6)
    axC.axis("off")
    axC.set_title("How it works", fontsize=11.5, fontweight="bold")
    txt = ("1. newd pulse \u2192 master starts streaming.\n\n"
           "2. Master drives valid_t + data;\n"
           "    slave replies with ready_t.\n\n"
           "3. 4 beats sent: data = din \u00d7 count.\n\n"
           "4. last_t marks the 4th (final) beat.\n\n"
           "5. Slave outputs dout = data while\n"
           "    receiving; last = last_t.")
    p = FancyBboxPatch((0.2, 0.2), 9.6, 5.4,
                       boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.6, edgecolor=ACCENT, facecolor="#fdf6e3")
    axC.add_patch(p)
    axC.text(0.55, 2.9, txt, ha="left", va="center", fontsize=9.5, color="#333333")

    out = OUT / "diagram_axis_top.png"
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
