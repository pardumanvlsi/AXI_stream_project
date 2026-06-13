"""Generate an explanatory diagram for the AXI4-Stream FIFO (axis_fifo).

PPT-ready PNG with four panels:
  (a) I/O block diagram (slave write port, master read port)
  (b) Circular FIFO memory with wr_ptr / rd_ptr and parallel arrays
  (c) Write / Read condition logic (full / empty, count)
  (d) Key facts / behaviour notes

Output: figures/diagram_axis_fifo.png
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge, Circle

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


def box(ax, x, y, w, h, text, *, fc=LIGHT, ec=PRIMARY, fs=10, bold=False, tc="black"):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.6, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color=tc, zorder=4)


def arrow(ax, x1, y1, x2, y2, *, color=GREY, lw=1.8, style="-|>", conn="arc3,rad=0"):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, connectionstyle=conn,
                        mutation_scale=15, linewidth=lw, color=color, zorder=2)
    ax.add_patch(a)


def main():
    fig = plt.figure(figsize=(14, 8.6))
    fig.suptitle("AXI4-Stream FIFO (axis_fifo) — Structure & Operation",
                 fontsize=16, fontweight="bold", color=PRIMARY, y=0.98)

    # =====================================================================
    # (a) I/O block diagram
    # =====================================================================
    axA = fig.add_axes([0.03, 0.52, 0.45, 0.40])
    axA.set_xlim(0, 10)
    axA.set_ylim(0, 8)
    axA.axis("off")
    axA.set_title("(a)  Module I/O", fontsize=12, fontweight="bold")

    box(axA, 3.3, 1.1, 3.4, 5.6, "", fc="#f7f9fc", ec=PRIMARY)
    axA.text(5.0, 6.25, "axis_fifo", fontsize=12, fontweight="bold",
             color=PRIMARY, ha="center")
    box(axA, 3.6, 3.7, 2.8, 1.6, "16-deep\nFIFO\n(d / keep / last)", fc=LIGHT,
        ec=PRIMARY, fs=9, bold=True)
    box(axA, 3.6, 2.0, 2.8, 1.0, "count / ptrs\nfull · empty", fc=LIGHT2,
        ec=AMBER, fs=8.5, bold=True)

    # slave (write) inputs
    s_in = [("s_axis_tvalid", 6.2), ("s_axis_tdata[7:0]", 5.4),
            ("s_axis_tkeep", 4.6), ("s_axis_tlast", 3.8)]
    for name, y in s_in:
        box(axA, 0.1, y - 0.26, 2.7, 0.52, name, fc=PINK, ec=ACCENT, fs=8)
        arrow(axA, 2.8, y, 3.3, y, color=ACCENT)
    box(axA, 0.1, 1.7, 2.7, 0.52, "aclk / aresetn", fc="#ededed", ec=GREY, fs=8)
    arrow(axA, 2.8, 1.96, 3.3, 1.96, color=GREY)
    axA.text(1.45, 6.95, "SLAVE write port", fontsize=8.5, color=ACCENT,
             ha="center", fontweight="bold")

    # master (read) outputs
    m_out = [("m_axis_tvalid", 6.0), ("m_axis_tdata[7:0]", 5.2),
             ("m_axis_tkeep", 4.4), ("m_axis_tlast", 3.6)]
    for name, y in m_out:
        box(axA, 7.2, y - 0.26, 2.7, 0.52, name, fc=LIGHT3, ec=GREEN, fs=8)
        arrow(axA, 6.7, y, 7.2, y, color=GREEN)
    box(axA, 7.2, 2.6, 2.7, 0.52, "m_axis_tready", fc=LIGHT3, ec=GREEN, fs=8)
    arrow(axA, 7.2, 2.86, 6.7, 2.86, color=GREEN)  # tready is an input (S<-M)
    axA.text(8.55, 6.75, "MASTER read port\n(to mux)", fontsize=8.5, color=GREEN,
             ha="center", fontweight="bold")

    # =====================================================================
    # (b) Circular FIFO memory
    # =====================================================================
    axB = fig.add_axes([0.52, 0.50, 0.45, 0.43])
    axB.set_xlim(-1.6, 1.6)
    axB.set_ylim(-1.6, 1.7)
    axB.axis("off")
    axB.set_title("(b)  Circular Buffer (16 slots \u00d7 3 arrays)",
                  fontsize=12, fontweight="bold")

    n = 16
    r_out, r_in = 1.35, 0.85
    filled = set(range(3, 9))  # example: slots 3..8 hold data
    wr_idx, rd_idx = 9, 3
    for i in range(n):
        a0 = 90 - i * 360 / n
        a1 = 90 - (i + 1) * 360 / n
        fc = LIGHT3 if i in filled else "white"
        w = Wedge((0, 0), r_out, a1, a0, width=r_out - r_in,
                  facecolor=fc, edgecolor=PRIMARY, linewidth=1.1, zorder=2)
        axB.add_patch(w)
        am = np.deg2rad((a0 + a1) / 2)
        rm = (r_out + r_in) / 2
        axB.text(rm * np.cos(am), rm * np.sin(am), str(i), ha="center",
                 va="center", fontsize=7, color=DK, zorder=3)
    axB.text(0, 0.18, "mem_d[16]", ha="center", fontsize=9, fontweight="bold",
             color=PRIMARY)
    axB.text(0, -0.12, "mem_k[16]", ha="center", fontsize=8, color=GREY)
    axB.text(0, -0.40, "mem_l[16]", ha="center", fontsize=8, color=GREY)

    def ptr(idx, label, color):
        a = np.deg2rad(90 - (idx + 0.5) * 360 / n)
        x0, y0 = 1.58 * np.cos(a), 1.58 * np.sin(a)
        x1, y1 = (r_out + 0.02) * np.cos(a), (r_out + 0.02) * np.sin(a)
        arrow(axB, x0, y0, x1, y1, color=color, lw=2.0)
        axB.text(1.72 * np.cos(a), 1.72 * np.sin(a), label, ha="center",
                 va="center", fontsize=8.5, color=color, fontweight="bold")
    ptr(wr_idx, "wr_ptr\n(write)", ACCENT)
    ptr(rd_idx, "rd_ptr\n(read)", GREEN)
    axB.text(0, -1.55, "write @ wr_ptr++   \u2022   read @ rd_ptr++   (wrap-around)",
             ha="center", fontsize=8, color=DK, style="italic")

    # =====================================================================
    # (c) Condition logic
    # =====================================================================
    axC = fig.add_axes([0.03, 0.05, 0.50, 0.36])
    axC.set_xlim(0, 12)
    axC.set_ylim(0, 6.5)
    axC.axis("off")
    axC.set_title("(c)  Per-Clock Decision (priority)", fontsize=12, fontweight="bold")

    box(axC, 4.3, 5.5, 3.4, 0.85, "posedge aclk", fc=PRIMARY, ec=PRIMARY,
        fs=10, bold=True, tc="white")
    box(axC, 0.3, 3.8, 3.4, 0.9, "aresetn == 0\n\u2192 clear ptrs/count,\nzero memory",
        fc=PINK, ec=ACCENT, fs=8.5)
    box(axC, 4.3, 3.8, 3.4, 0.9, "else if tvalid & !full\n\u2192 WRITE\nwr_ptr++, count++",
        fc=LIGHT, ec=PRIMARY, fs=8.5, bold=True)
    box(axC, 8.3, 3.8, 3.4, 0.9, "else if tready & !empty\n\u2192 READ\nrd_ptr++, count--",
        fc=LIGHT3, ec=GREEN, fs=8.5, bold=True)
    arrow(axC, 5.2, 5.5, 2.0, 4.7, color=GREY)
    arrow(axC, 6.0, 5.5, 6.0, 4.7, color=GREY)
    arrow(axC, 6.8, 5.5, 10.0, 4.7, color=GREY)

    box(axC, 1.0, 1.7, 4.4, 1.0, "full  = (count == 15)\nempty = (count == 0)",
        fc=LIGHT2, ec=AMBER, fs=9.5, bold=True)
    box(axC, 6.4, 1.7, 4.4, 1.0,
        "READ and WRITE are\nmutually exclusive\n(write has priority)",
        fc="#fdf6e3", ec=ACCENT, fs=9)
    axC.text(6.0, 0.7, "Only ONE of reset / write / read happens each clock edge.",
             ha="center", fontsize=8.5, color=DK, style="italic")

    # =====================================================================
    # (d) Notes
    # =====================================================================
    axD = fig.add_axes([0.55, 0.05, 0.42, 0.36])
    axD.set_xlim(0, 10)
    axD.set_ylim(0, 6.5)
    axD.axis("off")
    axD.set_title("(d)  Key Behaviour", fontsize=12, fontweight="bold")
    p = FancyBboxPatch((0.2, 0.2), 9.6, 5.7,
                       boxstyle="round,pad=0.02,rounding_size=0.05",
                       linewidth=1.6, edgecolor=PRIMARY, facecolor="#f7f9fc")
    axD.add_patch(p)
    txt = ("\u2022 Synchronous FIFO: write & read on same aclk.\n\n"
           "\u2022 Buffers TDATA, TKEEP, TLAST together so\n"
           "   packet framing is preserved end-to-end.\n\n"
           "\u2022 Depth: 16 entries (5-bit ptrs/count).\n\n"
           "\u2022 full at count==15, empty at count==0\n"
           "   provide back-pressure / under-run guard.\n\n"
           "\u2022 Decouples upstream slave from downstream\n"
           "   mux master (rate matching).")
    axD.text(0.55, 3.0, txt, ha="left", va="center", fontsize=9.5, color="#222222")

    out = OUT / "diagram_axis_fifo.png"
    fig.savefig(out, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
