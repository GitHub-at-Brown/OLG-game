import matplotlib.pyplot as plt
import numpy as np

def replicate_secular_stagnation_figure():
    # Use a built-in style for a design-friendly look.
    plt.style.use('seaborn')
    plt.rcParams.update({'font.size': 11, 'axes.labelweight': 'bold'})
    
    # ---------------------------------------------------
    # 1. Set up figure and axes
    # ---------------------------------------------------
    fig, ax = plt.subplots(figsize=(6.8, 4.5), dpi=100)
    ax.set_xlim(0.20, 0.30)
    ax.set_ylim(0.80, 1.20)
    ax.set_xticks(np.arange(0.20, 0.31, 0.02))
    ax.set_yticks(np.arange(0.80, 1.21, 0.05))
    ax.set_xlabel("Loans")
    ax.set_ylabel("Gross real interest rate")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    
    # ---------------------------------------------------
    # 2. Define the red (Loan supply) curves.
    #
    # We use a quadratic function f(t) = 113.45*t² + 20*t + 1.20,
    # with t = (x - h). For S₂ and S₃ we set:
    #   • S₂: h = 0.245 (so S₂(0.245)=1.20)
    #   • S₃: h = 0.280 (i.e. original 0.250 shifted right by 0.03)
    # For the dotted red curve S₁ we re-fit a quadratic so that:
    #   S₁(0.223) = 1.20 (top remains) and S₁(0.150) = 0.80
    # (Note: only the portion with x ≥ 0.20 is plotted.)
    # ---------------------------------------------------
    def f(t):
        return 113.45 * t**2 + 20 * t + 1.20

    def S2(x):
        return f(x - 0.245)
    
    def S3(x):
        return f(x - 0.280)
    
    # For S₁, solve for A in: A*(Δx)² + 20*(Δx) + 1.20 = 0.80 at Δx = (0.150-0.223) = -0.073.
    # That gives A ≃ 198.9.
    def S1(x):
        return 198.9 * (x - 0.223)**2 + 20 * (x - 0.223) + 1.20

    # Domains for the red curves:
    x_S1 = np.linspace(0.20, 0.223, 200)  # dotted red (S₁) visible portion
    x_S2 = np.linspace(0.222, 0.245, 200)  # solid red (S₂)
    x_S3 = np.linspace(0.257, 0.280, 200)  # solid red (S₃)
    
    # ---------------------------------------------------
    # 3. Define the blue (Loan demand) curves over the full domain [0.20, 0.30].
    #    Let D₁ pass through (0.20, 1.20) and (0.30, 0.80) with slight curvature;
    #    then D₂ = D₁ + 0.10.
    # ---------------------------------------------------
    def D1(x):
        return 1.20 - 4*(x - 0.20) - 10*(x - 0.20)*(0.30 - x)
    def D2(x):
        return D1(x) + 0.10
    x_blue = np.linspace(0.20, 0.30, 300)
    
    # ---------------------------------------------------
    # 4. Plot the curves.
    # ---------------------------------------------------
    # Plot red curves:
    ax.plot(x_S1, S1(x_S1), color="red", linestyle=":", linewidth=2)  # dotted S₁ (moved left)
    ax.plot(x_S2, S2(x_S2), color="red", linestyle="-", linewidth=2)   # solid S₂ (middle)
    ax.plot(x_S3, S3(x_S3), color="red", linestyle="-", linewidth=2)   # solid S₃ (right, shifted right)
    
    # Plot blue curves:
    ax.plot(x_blue, D1(x_blue), color="blue", linestyle="-", linewidth=2)
    ax.plot(x_blue, D2(x_blue), color="blue", linestyle="-", linewidth=2)
    
    # Horizontal dashed line at y = 1.00
    ax.axhline(y=1.00, color="grey", linestyle="--", linewidth=1)
    
    # ---------------------------------------------------
    # 5. Compute intersections.
    # We now compute three intersections and label them as follows:
    #   • Intersection A: S₁ ∩ D₂ (dotted red with upper blue)
    #   • Intersection B: S₂
