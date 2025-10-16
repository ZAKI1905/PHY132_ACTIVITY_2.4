# PHY 132 – Kirchhoff’s Rules Checker

This web app is part of the **PHY 132 (College Physics II)** labs at **Eastern Kentucky University (EKU)**.  
It lets students verify their **Kirchhoff’s Rules** equations and current calculations for assigned circuits.

The checker automatically computes expected results from circuit parameters — no stored answer keys — and logs submissions to a shared Google Sheet for instructor review.

---

## 🧩 What It Does

- Checks whether each student-entered **Kirchhoff equation** matches one of the valid loop or junction equations.
- Verifies that all three equations are **linearly independent**.
- Calculates the correct currents \(I_1, I_2, I_3\) from circuit parameters and compares them with the student’s answers.
- Accepts small numerical differences using tolerance bands:
  - ✅ Correct – within ±1 mA
  - ⚠️ Almost – within ±2 mA
  - ❌ Incorrect – outside tolerance
- Records each attempt (name, timestamp, results) to a Google Sheet through an Apps Script endpoint.

---

## ⚙️ How It Works

- Built with **[Streamlit](https://streamlit.io)** for an easy web interface.
- Circuit parameters for all 40 problem sets are stored in [`data/problems.json`](data/problems.json).
- The app dynamically solves each circuit using Kirchhoff’s laws; no pre-computed answers are visible.
- Circuit diagrams (`diags/circuit_set_#.png`) are auto-generated with **LaTeX + circuitikz** via a helper Python script.

---

## 🧮 File Structure
