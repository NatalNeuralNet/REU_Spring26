import math, cmath
import streamlit as st
from refractiveindex import RefractiveIndexMaterial
from display_functions import cached_build_tree

# Fresnel for theta in radians (complex ok)
def fresnel_RT_rad(N1, N2, theta1):
    sin1 = cmath.sin(theta1)
    cos1 = cmath.cos(theta1)

    sin2 = (N1 / N2) * sin1
    theta2 = cmath.asin(sin2)
    cos2 = cmath.cos(theta2)
    #theta2 = complex(round(theta2.real, 4), round(theta2.imag, 4))

    r_s = (N1 * cos1 - N2 * cos2) / (N1 * cos1 + N2 * cos2)
    r_p = (N2 * cos1 - N1 * cos2) / (N2 * cos1 + N1 * cos2)

    t_s = (2 * N1 * cos1) / (N1 * cos1 + N2 * cos2)
    t_p = (2 * N1 * cos1) / (N2 * cos1 + N1 * cos2)

    R_s = abs(r_s) ** 2
    R_p = abs(r_p) ** 2

    phi_rs = cmath.phase(r_s)
    phi_rp = cmath.phase(r_p)
    
    phi_ts = cmath.phase(t_s)
    phi_tp = cmath.phase(t_p)


    denom = (N1 * cos1).real
    if abs(denom) < 1e-15:
        T_s = float("nan")
        T_p = float("nan")
    else:
        factor = (N2 * cos2).real / denom
        T_s = factor * abs(t_s) ** 2
        T_p = factor * abs(t_p) ** 2

    return {
        "theta2": theta2,
        "Runpol": 0.5 * (R_s + R_p),
        "Tunpol": 0.5 * (T_s + T_p),
        "Rs": R_s, "Rp": R_p, "Ts": T_s, "Tp": T_p,
        "phi_rs" : phi_rs, "phi_rp" : phi_rp,
        "phi_ts" : phi_ts, "phi_tp" : phi_tp
    }
def round_complex(z, nd=4):
    return complex(round(z.real, nd), round(z.imag, nd))
