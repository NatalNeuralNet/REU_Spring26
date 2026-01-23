import streamlit as st
from pathlib import Path
from refractiveindex import RefractiveIndexMaterial
import pandas as pd
import math, cmath
import numpy as np
import matplotlib.pyplot as plt
from physics_functions import *
from display_functions import *



# Interpretation: currently have per-interface phase shifts, but not propagation phase through a finite-thickness layer, which is what creates interference.

# -----------------------------
# App UI
#   Select Intial Parameters
# -----------------------------
st.title("Film Layers")

col1, col2, col3 = st.columns(3)
with col1:
    medium = st.selectbox("Initial Medium", ["Air", "Vacuum"])
with col2:
    wavelength_nm = st.number_input("Wavelength (nm)", value=550.0, step=1.0)
with col3:
    max_layers = st.slider("Max coating layers", min_value=0, max_value=10, value=3, step=1)
col4, col5 = st.columns(2)    
with col4:
    substrate = st.selectbox("Substrate", ["Glass"])    
with col5:
    substrate_depth = st.number_input("Substrate Depth", value=100, step = 1)     
shelves, books_by_shelf, pages_by_shelf_book = cached_build_tree()
ensure_state(max_layers)


st.divider()

# -----------------------------
# Layer Customization
# -----------------------------
if max_layers == 0:
    st.info("Max coating layers is 0 — no coating selection needed. Medium + glass substrate will still be shown in the table.")
else:
    layer_num = int(st.session_state.current_layer)
    st.title(f"Layer {layer_num}")

    colA, colB, colC = st.columns(3)

    shelf = colA.selectbox("Shelf", shelves, key=f"shelf_sel_{layer_num}")
    books = books_by_shelf.get(shelf, [])
    book = colB.selectbox("Material (Book)", books, key=f"book_sel_{layer_num}")

    pages = pages_by_shelf_book.get((shelf, book), [])
    if not pages:
        colC.warning("No pages found for this shelf/book.")
        page = None
    else:
        page = colC.selectbox("Source (Page)", pages, key=f"page_sel_{layer_num}")

    if is_saved(layer_num):
        st.caption("✅ This coating layer is saved (saving again overwrites it).")
    else:
        st.caption("⚠️ Not saved yet — save to unlock 'Add next layer'.")

# -----------------------------
# Layers butto row
# -----------------------------
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 1])

with ctrl1:
    if st.button("Finalize/Fill", disabled=(max_layers == 0)):
        for layer_num in range(1, max_layers + 1):
            if layer_num not in st.session_state.layer_rows:
                st.session_state.layer_rows[layer_num] = empty_row(layer_num)
        st.success("Finalized: all remaining coating layers filled with N/A.")
        st.rerun()

# button to naviagte all layers
# I need to lock this similar to the next button to prevent going to non built layers
#with ctrl2:
#    st.session_state.current_layer = st.number_input(
#        "Current coating layer #",
#        min_value=1,
#        max_value=max_layers if max_layers > 0 else 1,
#        value=st.session_state.current_layer,
#        step=1,
#        disabled=(max_layers == 0),
#    )

with ctrl2:

    if st.button("← Previous"):
        st.session_state.current_layer -= 1
        st.rerun()

with ctrl3:
    if st.button("Save layer"):
        if not page:
            st.session_state.layer_rows[layer_num] = {
                "layer": layer_num,
                "shelf": shelf,
                "book": book,
                "page": None,
                "n": None,
                "k": None,
                "N": None,
                "error": "No pages"
            }
            st.warning("Saved as N/A because no page was available.")
            st.rerun()

        try:
            n, k, N, err = cached_get_nk(shelf, book, page, wavelength_nm)
            st.session_state.layer_rows[layer_num] = {
                "layer": layer_num,
                "shelf": shelf,
                "book": book,
                "page": page,
                "n": n,
                "k": k,
                "N": N,
                "error": err
            }
            st.success(f"Saved Coating Layer {layer_num}.")
            st.rerun()
        except Exception as e:
            st.session_state.layer_rows[layer_num] = {
                "layer": layer_num,
                "shelf": shelf,
                "book": book,
                "page": page,
                "n": None,
                "k": None,
                "N": None,
                "error": type(e).__name__
            }
            st.error(f"Layer {layer_num} failed: {type(e).__name__}")
            st.rerun()

with ctrl4:
    # lock next until current layer is saved
    if max_layers == 0:
        next_disabled = True
    else:
        layer_num = int(st.session_state.current_layer)
        next_disabled = (layer_num >= max_layers) or (not is_saved(layer_num))

    if st.button("Next ➜", disabled=next_disabled):
        st.session_state.current_layer += 1
        st.rerun()


st.divider()

# -----------------------------
# Table (medium + coatings + glass)
# -----------------------------
st.subheader("Layer table (medium + coatings + glass)")
table_rows = build_display_table(max_layers, medium, wavelength_nm)

df = pd.DataFrame(table_rows)
st.dataframe(df, use_container_width=True)

#Real
theta0_deg = 45
theta0_rad = math.radians(theta0_deg)

# Complex
theta0 = complex(math.radians(theta0_deg), 0.0)

#theta2 = complex(round(theta2.real, 4), round(theta2.imag, 4))

# Build complex N list (skip rows where n is missing)
N_list = []
for n_val, k_val in zip(df["n"], df["k"]):
    if pd.isna(n_val):
        N_list.append(None)
    else:
        kv = 0.0 if pd.isna(k_val) else float(k_val)
        N_list.append(complex(float(n_val), kv))

thetas_c = [theta0]   # complex Snell chain (uses full complex N)
thetas_r = [theta0]   # "real-only" Snell chain (uses Re(N) only)

interface_rows = []
reflectivity_rows = []
transmission_rows = []

for i in range(len(N_list) - 1):
    N1, N2 = N_list[i], N_list[i + 1]
    if N1 is None or N2 is None or abs(N2) < 1e-15:
        continue

    # --- complex case ---
    th1_c = thetas_c[i]
    out_c = fresnel_RT_rad(N1, N2, th1_c)
    th2_c = out_c["theta2"]
    thetas_c.append(th2_c)

    # --- real-only case ---
    N1r = N1.real
    N2r = N2.real
    th1_r = thetas_r[i]
    out_r = fresnel_RT_rad(N1r, N2r, th1_r)
    th2_r = out_r["theta2"]
    thetas_r.append(th2_r)

    # display angles in degrees (keep real part for readability)
    deg = 180 / math.pi
    interface_rows.append({
        "interface": i + 1,
        "N1": N1,
        "RE(θi)": (th1_r.real * deg),
        "θi_complex": round_complex(th1_c * deg, 4),
        "N2": N2,
        "θt complex": round_complex(th2_c * deg, 4),
        "RE(θt)": (th2_r.real * deg),
    })

    reflectivity_rows.append({
        "interface": i + 1,
        "Runpol_complex": out_c["Runpol"],
        "Rs_complex": out_c["Rs"],
        "Rp_complex": out_c["Rp"],
        "Runpol_real": out_r["Runpol"],
        "Rs_real": out_r["Rs"],
        "Rp_real": out_r["Rp"],
        "phi_rs_deg": math.degrees(out_c["phi_rs"]),
        "phi_rp_deg": math.degrees(out_c["phi_rp"]),
    })

    transmission_rows.append({
        "interface": i + 1,
        "Tunpol_complex": out_c["Tunpol"],
        "Ts_complex": out_c["Ts"],
        "Tp_complex": out_c["Tp"],
        "Tunpol_real": out_r["Tunpol"],
        "Ts_real": out_r["Ts"],
        "Tp_real": out_r["Tp"],
        "phi_ts_deg": math.degrees(out_c["phi_ts"]),
        "phi_tp_deg": math.degrees(out_c["phi_tp"]),
    })

st.subheader("Interface results")
st.dataframe(pd.DataFrame(interface_rows), use_container_width=True)
st.subheader("Reflectivity")
st.dataframe(pd.DataFrame(reflectivity_rows), use_container_width=True)
st.subheader("Transmission")
st.dataframe(pd.DataFrame(transmission_rows), use_container_width=True)


# ---------------------------------------
# Plot: points in (n,k) across the stack
# Size = |N|, Color = θ in that medium (real-n Snell)
# ---------------------------------------
st.subheader("Stack points in (n,k) space")

# Build labels from your table
labels = []
for idx, row in df.iterrows():
    if idx == 0:
        labels.append(str(row["book"]).capitalize())  # Air / Vacuum
    elif idx == len(df) - 1:
        labels.append("Glass")
    else:
        labels.append(f"Layer {int(row['layer'])}")

# Extract numeric n,k (skip rows with missing n)
n_vals = []
k_vals = []
lab_vals = []
for lab, n, k in zip(labels, df["n"], df["k"]):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        continue
    kv = 0.0 if (k is None or (isinstance(k, float) and pd.isna(k))) else float(k)
    n_vals.append(float(n))
    k_vals.append(kv)
    lab_vals.append(lab)

# Need at least 2 points to draw arrows/lines
if len(n_vals) < 2:
    st.info("Add at least two defined materials (n values) to show the (n,k) plot.")
else:
    n_pts = np.array(n_vals, dtype=float)
    k_pts = np.array(k_vals, dtype=float)

    # Real-n Snell for theta in each medium (for color)
    theta0_deg = 45.0  # or make this a Streamlit number_input if you want
    theta0_rad = math.radians(theta0_deg)
    n0 = n_pts[0]  # medium's n

    sin_const = n0 * math.sin(theta0_rad)
    arg = sin_const / np.maximum(1e-15, n_pts)
    arg = np.clip(arg, -1.0, 1.0)
    theta_deg_media = np.degrees(np.arcsin(arg))

    # Sizes from |N|
    Nmag = np.sqrt(n_pts**2 + k_pts**2)
    s_min, s_max = 120.0, 600.0
    denom = max(1e-12, float(Nmag.max() - Nmag.min()))
    sizes = s_min + (Nmag - Nmag.min()) / denom * (s_max - s_min)

    # Build the figure
    fig, ax = plt.subplots(figsize=(7, 5))

    # Connect points with dashed line
    ax.plot(n_pts, k_pts, linestyle="--", linewidth=1)

    # Draw arrows between consecutive points
    for i in range(len(n_pts) - 1):
        ax.annotate(
            "",
            xy=(n_pts[i+1], k_pts[i+1]),
            xytext=(n_pts[i], k_pts[i]),
            arrowprops=dict(arrowstyle="->", linestyle="--", lw=2),
        )

    sc = ax.scatter(n_pts, k_pts, s=sizes, c=theta_deg_media, edgecolors="k", zorder=3)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("θ in that medium (deg)")

    # Label each point
    for i, lab in enumerate(lab_vals):
        ax.text(
            n_pts[i], k_pts[i],
            f"  {lab}\n  |N|={Nmag[i]:.3g}\n  θ={theta_deg_media[i]:.2f}°",
            va="bottom"
        )

    ax.set_title(f"Stack points in (n,k) @ {wavelength_nm} nm\nSize=|N|, Color=θ (real-n Snell)")
    ax.set_xlabel("n")
    ax.set_ylabel("k")
    ax.grid(True)

    st.pyplot(fig, clear_figure=True)
