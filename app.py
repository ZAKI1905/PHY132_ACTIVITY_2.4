# app.py  (Kirchhoff Checker – refactored to match Resistor Checker style)
import streamlit as st
import json
import requests
import numpy as np
from datetime import datetime
from pathlib import Path

# =========================
# 🔧 CONFIG (edit as needed)
# =========================
# Tolerances
# Currents are entered in mA; we compare in mA.
TOL_I_MA          = 1.0     # within ±1 mA is considered correct
ALMOST_MULT       = 2.0     # “Almost” = within 2× tolerance
ATOL_EQ_COEFF     = 0.1     # absolute tolerance for equation coefficient comparisons
RTOL_EQ_COEFF     = 1e-3

# Apps Script endpoint is stored in Streamlit Secrets
# .streamlit/secrets.toml:
# [apps_script]
# kirchhoff_url = "https://script.google.com/macros/s/XXXX/exec"
APPS_SCRIPT_URL = st.secrets["apps_script"]["kirchhoff_url"]

# Data locations
PROBLEMS_PATH = Path("data/problems.json")  # maps "set_number" -> [V1, V2, R1, R2, R3]
JAVAB_PATH    = Path("data/javab.json")     # maps "set_number" -> [I1_mA, I2_mA, I3_mA] (optional)

# =========================
# 🧮 Helpers
# =========================
def verdict_icon(ok: bool, almost: bool = False) -> str:
    if ok:
        return "✅"
    if almost:
        return "⚠️"
    return "❌"

def is_within(student_val: float, target_val: float, tol_abs: float) -> bool:
    return abs(student_val - target_val) <= tol_abs

def almost_within(student_val: float, target_val: float, tol_abs: float) -> bool:
    return (not is_within(student_val, target_val, tol_abs)) and is_within(student_val, target_val, tol_abs * ALMOST_MULT)

def log_submission(payload: dict):
    try:
        r = requests.post(APPS_SCRIPT_URL, json=payload, timeout=8)
        return r.status_code, r.text
    except Exception as e:
        return -1, str(e)

# ----- Equation helpers -----
def _canonicalize(eq_vec: np.ndarray) -> np.ndarray:
    """
    Make equations scale- and sign-invariant:
    - divide by L2 norm (if nonzero) to remove global scale
    - flip sign so first nonzero coefficient is >= 0
    """
    v = np.array(eq_vec, dtype=np.float64)
    # If all zeros, return as-is
    if not np.any(np.abs(v) > 0):
        return v
    # Normalize by L2
    norm = np.linalg.norm(v)
    if norm > 0:
        v = v / norm
    # Flip sign to make first nonzero >= 0
    for x in v:
        if abs(x) > 0:
            if x < 0:
                v = -v
            break
    return v

def normalize_equation(eq):
    """Public wrapper: accepts list/tuple -> returns canonicalized np.ndarray."""
    return _canonicalize(np.array(eq, dtype=np.float64))

def compare_equations(student_eqs, expected_eqs):
    """
    Check if each student equation matches any expected equation
    under scale/sign invariance within tolerances.
    """
    stud_norm = [normalize_equation(eq) for eq in student_eqs]
    exp_norm  = [normalize_equation(eq) for eq in expected_eqs]

    matches = []
    for s in stud_norm:
        match_found = any(np.allclose(s, e, rtol=RTOL_EQ_COEFF, atol=ATOL_EQ_COEFF) for e in exp_norm)
        matches.append(match_found)
    return matches

def check_linear_independence(equations):
    """Check linear independence on the coefficient matrix (exclude constant terms)."""
    coeff_matrix = np.array([eq[:-1] for eq in equations], dtype=np.float64)
    rank = np.linalg.matrix_rank(coeff_matrix)
    return rank == len(equations)

# ----- Kirchhoff system -----
def compute_kirchhoff_coefficients(V1, V2, R1, R2, R3):
    # Equations in the form: A*I1 + B*I2 + C*I3 + D = 0
    # Junction: I1 - I2 - I3 = 0
    eq1 = ( 1.0, -1.0, -1.0, 0.0)
    # Left loop: V1 - R3*I3 - R1*I1 = 0  => (-R1, 0, -R3, V1)
    eq2 = (-float(R1), 0.0, -float(R3), float(V1))
    # Right loop: V2 + R2*I2 - R3*I3 = 0 => (0, R2, -R3, -V2)
    eq3 = (0.0, float(R2), -float(R3), -float(V2))
    # Big loop: V1 - R2*I2 - V2 - R1*I1 = 0 => (-R1, -R2, 0, V1 - V2)
    eq4 = (-float(R1), -float(R2), 0.0, float(V1) - float(V2))
    return [eq1, eq2, eq3, eq4]

def solve_currents_from_params(V1, V2, R1, R2, R3):
    """
    Solve the 3-unknown (I1,I2,I3) system using three independent equations.
    We use: Junction (eq1), Left loop (eq2), Right loop (eq3).
    """
    eqs = compute_kirchhoff_coefficients(V1, V2, R1, R2, R3)
    A = np.array([eqs[0][0:3], eqs[1][0:3], eqs[2][0:3]], dtype=np.float64)  # coefficients
    b = -np.array([eqs[0][3],     eqs[1][3],     eqs[2][3]], dtype=np.float64)  # constants moved to RHS
    I = np.linalg.solve(A, b)  # in amperes if V,Ω
    return I  # A

# =========================
# 📦 Load data
# =========================
with open(PROBLEMS_PATH, "r") as f:
    PROBLEMS = json.load(f)  # "1": [V1, V2, R1, R2, R3]

JAVAB = {}
if JAVAB_PATH.exists():
    with open(JAVAB_PATH, "r") as f:
        JAVAB = json.load(f)  # "1": [I1_mA, I2_mA, I3_mA]

# =========================
# 🖥️ UI
# =========================
st.set_page_config(page_title="PHY 132 – Kirchhoff Checker", page_icon="🔌")
st.title("PHY 132 – Kirchhoff’s Rules Checker")
st.write("Enter your equations and currents for your assigned circuit. You’ll get instant feedback; correct submissions are recorded for credit.")

with st.expander("📘 Kirchhoff Recap"):
    st.markdown(
        "**KCL:** net current into any node is zero.  \n"
        "**KVL:** algebraic sum of potential differences around any closed loop is zero.  \n"
        "We use the standard sign convention: passive sign for resistor drops and source polarities as drawn."
    )

# Name / comment
colA, colB = st.columns(2)
with colA:
    student_name    = st.text_input("Name (for credit)")
with colB:
    student_comment = st.text_input("Comment (optional)")

# Problem set
set_number = st.number_input("Enter your problem set number (1–40)", min_value=1, max_value=40, step=1)
ps = PROBLEMS.get(str(int(set_number)))
if not ps:
    st.stop()

V1, V2, R1, R2, R3 = map(float, ps)

# Diagram
diagram_path = f"https://raw.githubusercontent.com/ZAKI1905/phy132-kirchhoff-checker/main/Diagrams/circuit_set_{int(set_number)}.png"
st.image(diagram_path, caption=f"Problem Set {int(set_number)} Diagram", use_container_width=True)

# Expected equations
expected_eqs = compute_kirchhoff_coefficients(V1, V2, R1, R2, R3)

# ---- Equations input ----
st.subheader("Enter your Kirchhoff equation coefficients in the following format:")

st.latex(r"A \cdot I_1 \,+ \, B \cdot I_2 \, +\,  C \cdot I_3\,  +\,  D \, =\,  0")

st.write("Where:")
st.markdown(r"""
- $A, B, C$ are the coefficients of $I_1, I_2, I_3$, respectively.  
- $D$ is the constant term (voltage sum).
""", unsafe_allow_html=True)

coeff_labels = ["I1", "I2", "I3", "Constant (D)"]
student_eqs = []
for i in range(3):
    with st.container(border=True):
        st.write(f"**Equation {i+1}**")
        row = [st.number_input(f"Eq {i+1}: Coefficient of {label}", key=f"eq{i}_{label}", value=0.0, step=0.1, format="%.2f") for label in coeff_labels]
        student_eqs.append(row)

if st.button("Check my equations"):
    matches = compare_equations(student_eqs, expected_eqs)
    indep   = check_linear_independence(student_eqs)

    st.markdown("### Equation Results")
    for i, m in enumerate(matches, start=1):
        st.write(f"{verdict_icon(m)} Equation {i}")

    if not indep:
        st.warning("⚠️ Your three equations are not linearly independent (you may have repeated a loop or combined equations).")

    # Log equations attempt
    payload_eq = {
        "Time Stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": student_name,
        "Comment": student_comment,
        "Set #": str(int(set_number)),
        "Student Eqs (JSON)": json.dumps(student_eqs),
        "Result (eqs)": "All match" if all(matches) and indep else "Partial/Not independent" if any(matches) else "No match",
        "sheet": "Kirchhoff_Equations"  # handle in Apps Script if you route by sheet
    }
    status, resp = log_submission(payload_eq)
    if status != 200:
        st.info("Note: logging issue encountered. Your local check ran fine—please try again soon or notify your instructor.")
        st.caption(f"(Logging status {status}: {resp})")

# ---- Currents input ----
st.subheader("Enter your calculated currents (mA)")
c1, c2, c3 = st.columns(3)
with c1:
    I1_mA = st.number_input("I1 (mA)", min_value=0.0, step=0.01, format="%.2f")
with c2:
    I2_mA = st.number_input("I2 (mA)", min_value=0.0, step=0.01, format="%.2f")
with c3:
    I3_mA = st.number_input("I3 (mA)", min_value=0.0, step=0.01, format="%.2f")

def expected_currents_mA(set_no: int):
    """Return expected (I1,I2,I3) in mA, preferring javab.json; else compute from parameters."""
    key = str(int(set_no))
    if key in JAVAB:
        return list(map(float, JAVAB[key]))
    # Compute from parameters (V in V, R in Ω -> I in A -> convert to mA)
    I_A = solve_currents_from_params(V1, V2, R1, R2, R3)
    return (I_A * 1e3).tolist()

if st.button("Check my currents"):
    I_expected_mA = expected_currents_mA(set_number)

    i1_ok     = is_within(I1_mA, I_expected_mA[0], TOL_I_MA)
    i2_ok     = is_within(I2_mA, I_expected_mA[1], TOL_I_MA)
    i3_ok     = is_within(I3_mA, I_expected_mA[2], TOL_I_MA)

    i1_almost = almost_within(I1_mA, I_expected_mA[0], TOL_I_MA)
    i2_almost = almost_within(I2_mA, I_expected_mA[1], TOL_I_MA)
    i3_almost = almost_within(I3_mA, I_expected_mA[2], TOL_I_MA)

    all_correct = i1_ok and i2_ok and i3_ok
    any_almost  = i1_almost or i2_almost or i3_almost

    st.markdown("### Current Results")
    st.write(f"{verdict_icon(i1_ok, i1_almost)} **I1**")
    st.write(f"{verdict_icon(i2_ok, i2_almost)} **I2**")
    st.write(f"{verdict_icon(i3_ok, i3_almost)} **I3**")

    if all_correct:
        st.success("✅ All correct! Your submission has been recorded for full credit.")
        result_label = "Correct"
    elif any_almost:
        st.warning("⚠️ Close. Some currents are within 2× tolerance but not within the main tolerance.")
        result_label = "Almost"
    else:
        st.error("❌ Not quite. Re-check your equations/signs and try again.")
        result_label = "Incorrect"

    # Log to Google Sheets via Apps Script
    payload = {
        "Time Stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": student_name,
        "Comment": student_comment,
        "Set #": str(int(set_number)),
        "I1 (mA)": I1_mA,
        "I2 (mA)": I2_mA,
        "I3 (mA)": I3_mA,
        "I1_exp (mA)": I_expected_mA[0],
        "I2_exp (mA)": I_expected_mA[1],
        "I3_exp (mA)": I_expected_mA[2],
        "Tolerance_mA": TOL_I_MA,
        "Result": result_label,
        "sheet": "Kirchhoff_Currents"  # handle in Apps Script if routing by sheet
    }
    status, resp = log_submission(payload)
    if status != 200:
        st.info("Note: logging issue encountered. Your local check ran fine—please try again soon or notify your instructor.")
        st.caption(f"(Logging status {status}: {resp})")

# Footer
st.markdown("""
---
<div style="display:flex;justify-content:space-between;align-items:center;">
  <div>
    Built for <b>PHY 132 – College Physics II</b> at Eastern Kentucky University.<br>
    Contact: <b>Professor Zakeri</b> (m.zakeri@eku.edu)
  </div>
  <div>
    <img src="https://raw.githubusercontent.com/ZAKI1905/phy132-kirchhoff-checker/main/img/PrimaryLogo_Maroon.png" width="150">
  </div>
</div>
""", unsafe_allow_html=True)