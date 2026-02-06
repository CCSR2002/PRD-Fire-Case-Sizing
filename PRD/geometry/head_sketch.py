import numpy as np
import matplotlib.pyplot as plt

from heads import ASMEFDHead, Elliptical2to1Head, HemisphericalHead

def plot_single_head(head, label, color):
    h_top = getattr(head, "h3", head.h2)
    hs = np.linspace(head.h1, h_top, 10000)
    rs = [head.radius_at_height(h) for h in hs]

    fig, ax = plt.subplots(figsize=(6, 8))
    ax.plot(rs, hs, color=color, label=label)
    ax.plot([-r for r in rs], hs, color=color)

    ax.set_aspect("equal")
    ax.set_xlabel("Radius (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title(f"{label} Head Profile")
    ax.legend()
    ax.grid(True)
    plt.show()

# ---------------------------------------------------------
# Instantiate heads
# ---------------------------------------------------------
diameter = 1.0
thickness = 0.015

fd   = ASMEFDHead(diameter, thickness)
ell  = Elliptical2to1Head(diameter, thickness)
hemi = HemisphericalHead(diameter, thickness)

# ---------------------------------------------------------
# Plot each head separately
# ---------------------------------------------------------
plot_single_head(fd,   "ASME F&D",          "blue")
plot_single_head(ell,  "ASME 2:1 Ellipsoidal", "green")
plot_single_head(hemi, "Hemispherical",     "red")

