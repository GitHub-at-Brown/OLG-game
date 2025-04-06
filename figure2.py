import numpy as np
import matplotlib.pyplot as plt

def replicate_secular_stagnation_figure():
    """
    Replicates the economics figure showing:
    - A dotted red 'Aggregate supply' curve with a kink at x=1.00
    - Two 'Aggregate demand' curves: AD1 (solid, navy) and AD2 (dashed, purple)
    - A horizontal line at y=1.00
    - Axis labels, ticks from 0.80 to 1.20 on the y-axis and ~0.80 to 1.05 on x-axis
    - Text labels: 'Aggregate supply', 'AD1', 'AD2', 'Deflation steady state'
    - Two arrows pointing to the deflation steady‐state intersection
    - Overall format matching the reference figure exactly
    """

    # --- FIGURE SETUP ---
    # Set figure size so that proportions match typical academic plots
    # Adjust dpi or inches as needed for a visually identical layout
    fig, ax = plt.subplots(figsize=(6,4), dpi=100)

    # --- DATA FOR CURVES ---
    # We'll define piecewise data for the Aggregate Supply (AS) curve
    # so it has a kink at x=1.0. The y-values are chosen to match the shape in the figure.
    
    # For x < 1.0, slope negative from (0.80, 1.15) down to (1.00, 0.90)
    x_as_left = np.linspace(0.80, 1.00, 50)
    y_as_left = np.linspace(1.15, 0.90, 50)
    
    # For x > 1.0, slope positive from (1.00, 0.90) up to (1.05, 1.20)
    x_as_right = np.linspace(1.00, 1.05, 20)
    y_as_right = np.linspace(0.90, 1.20, 20)

    # AD1: from (0.80, 0.85) to (1.00, 0.95) (solid navy)
    x_ad1 = np.linspace(0.80, 1.00, 50)
    y_ad1 = np.linspace(0.85, 0.95, 50)

    # AD2: from (0.80, 0.90) to (1.00, 1.00) (dashed purple)
    x_ad2 = np.linspace(0.80, 1.00, 50)
    y_ad2 = np.linspace(0.90, 1.00, 50)

    # --- PLOT THE CURVES ---
    # Aggregate Supply (dotted red)
    ax.plot(x_as_left, y_as_left, color='red', linestyle=':', linewidth=2, label='_nolegend_')
    ax.plot(x_as_right, y_as_right, color='red', linestyle=':', linewidth=2, label='_nolegend_')

    # AD1 (solid, navy)
    ax.plot(x_ad1, y_ad1, color='navy', linestyle='-', linewidth=2, label='_nolegend_')

    # AD2 (dashed, purple)
    ax.plot(x_ad2, y_ad2, color='purple', linestyle='--', linewidth=2, label='_nolegend_')

    # --- HORIZONTAL LINE AT Y=1.00 ---
    ax.axhline(y=1.00, color='black', linestyle='-', linewidth=1)

    # --- AXIS LIMITS & TICKS ---
    ax.set_xlim(0.80, 1.05)
    ax.set_ylim(0.80, 1.20)
    
    # Ticks at 0.80, 0.85, 0.90, 0.95, 1.00, 1.05 (x) and up to 1.20 (y)
    x_ticks = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05]
    y_ticks = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]
    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    
    # --- AXIS LABELS ---
    ax.set_xlabel("Output", fontsize=12)
    ax.set_ylabel("Gross inflation rate", fontsize=12)

    # --- TEXT LABELS FOR CURVES ---
    # Position them so they appear near their respective lines
    # 'Aggregate supply' near top right
    ax.text(1.01, 1.06, "Aggregate supply", color='red', fontsize=10, rotation=0,
            va='bottom', ha='left')

    # 'AD2' in between AD1 and top line
    ax.text(0.90, 0.965, "AD2", color='purple', fontsize=10, va='center', ha='left')

    # 'AD1' slightly below that
    ax.text(0.90, 0.93, "AD1", color='navy', fontsize=10, va='center', ha='left')

    # --- DEFLECTION STEADY STATE ANNOTATION ---
    # The figure has "Deflation steady state" text with two arrows pointing around the lower intersection.
    # We'll place the text around (0.82, 0.88) and draw two arrows to points near the AD1 curve.
    ax.text(0.82, 0.88, "Deflation\nsteady state", fontsize=10, ha='left', va='top')

    # Draw arrows from that text to two nearby points
    # Just approximate them so that visually they match the figure.
    ax.annotate(
        "", 
        xy=(0.85, 0.90),  # arrow tip
        xytext=(0.82, 0.88),  # text location
        arrowprops=dict(arrowstyle="->", linewidth=1),
    )
    ax.annotate(
        "", 
        xy=(0.86, 0.88),  # second arrow tip
        xytext=(0.82, 0.88),  # text location
        arrowprops=dict(arrowstyle="->", linewidth=1),
    )

    # --- FINAL FORMATTING ---
    # Remove top and right spines (as is common in academic figures) if desired:
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)

    # Save as JPG at sufficiently high resolution to ensure clarity
    plt.tight_layout()
    plt.savefig("replicated_secular_stagnation_figure.jpg", dpi=300)
    plt.show()

if __name__ == "__main__":
    replicate_secular_stagnation_figure()
