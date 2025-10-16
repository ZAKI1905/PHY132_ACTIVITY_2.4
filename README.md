# PHY 132 – Kirchhoff’s Rules Checker

This web app is part of the **PHY 132 (College Physics II)** labs at **Eastern Kentucky University (EKU)**.  
It lets students verify their **Kirchhoff’s Rules** equations and current calculations for assigned circuits.

The checker automatically computes expected results from circuit parameters — no stored answer keys — and logs submissions to a Google Sheet for instructor review.

---

## What It Does

- Checks whether each student-entered **Kirchhoff equation** matches one of the valid loop or junction equations.
- Verifies that the three submitted equations are **linearly independent**.
- Calculates the correct currents \(I_1, I_2, I_3\) from circuit parameters and compares them with the student’s answers.
- Uses tolerance bands for feedback:
  - ✅ **Correct** – within ±1 mA
  - ⚠️ **Almost** – within ±2 mA
  - ❌ **Incorrect** – outside tolerance
- Records each attempt (name, timestamp, results) to a Google Sheet via a Google Apps Script endpoint.

---

## How It Works

- Built with **Streamlit** for a simple web interface.
- Circuit parameters for 40 problem sets are stored in `data/problems.json` as `[V1, V2, R1, R2, R3]`.
- The app **solves** each circuit on the fly with Kirchhoff’s laws (no exposed answer keys).
- Circuit diagrams (`diags/circuit_set_#.png`) are generated with **LaTeX + circuitikz** using `generate_diagrams.py`.

---

## File Structure

phy132-kirchhoff-checker/
│
├── app.py # main Streamlit app
├── data/
│ └── problems.json # 40 sets: [V1, V2, R1, R2, R3]
├── diags/
│ ├── circuit_set_1.png # prebuilt circuit diagrams
│ └── …
├── generate_diagrams.py # LaTeX → PNG generator (keeps only PNGs)
└── .streamlit/
└── secrets.toml # private URLs and optional secret

---

## Deployment (Streamlit Cloud)

### 1) Create a new GitHub repository

Recommended name: `phy132-kirchhoff-checker`

Include:

- `app.py`
- `data/problems.json`
- `diags/` (with the 40 PNG circuit images)
- `generate_diagrams.py` (optional, if you want to regenerate diagrams)

> Do **not** include any solutions. The app computes answers internally.

### 2) Configure Streamlit Secrets

Add under **Settings → Secrets** in Streamlit Cloud:

````toml
[apps_script]
kirchhoff_url = "https://script.google.com/macros/s/XXXX/exec"
shared_secret = "OPTIONAL-STRING"


If you also use the same spreadsheet for the resistor checker, you may add:

resistor_url = "https://script.google.com/macros/s/YYYY/exec"

### 3) Deploy

1. Open [https://share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select this repository
4. Set **Main file** to `app.py`
5. Click **Deploy**

Your app will be live at a URL like:
https://-phy132-kirchhoff-checker.streamlit.app


Share that link with students.

---

## Google Sheet Integration

This app and the **Resistor Power Checker (Activity 2.2)** can log into the **same** Google Sheet.
The Apps Script routes rows to different tabs based on the `sheet` field in the POST request:

- `2.2-Resistors`
- `Kirchhoff_Equations`
- `Kirchhoff_Currents`

The script automatically creates tabs if they don’t exist and expands headers whenever new fields are added.

---

## Instructor Tools

- **To regenerate circuit diagrams**, run:

```bash
python generate_diagrams.py


This keeps only .png files and deletes all temporary LaTeX/PDF artifacts.

- **To change problem sets**, edit the parameters in:
	data/problems.json

and redeploy to Streamlit Cloud.

---

## Topics

`physics` `circuits` `kirchhoff` `streamlit` `eku` `education` `teaching`

---

## License

For educational use in PHY 132 at Eastern Kentucky University.
Feel free to adapt or fork this project for your own teaching needs.
````
