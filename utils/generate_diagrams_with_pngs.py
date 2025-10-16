#!/usr/bin/env python3
import os
import json
import shutil
import subprocess
from pathlib import Path

# -----------------------------
# Paths / config
# -----------------------------
PROBLEMS_JSON = Path("../data/problems.json")   # {"1":[V1,V2,R1,R2,R3], ...}
OUTPUT_DIR    = Path("../diags")                # final PNGs live here
BUILD_DIR     = OUTPUT_DIR / "_build"        # temporary LaTeX build dir
DENSITY_DPI   = "300"                        # PNG render resolution

# -----------------------------
# LaTeX template
# -----------------------------
STANDALONE_TEX = r"""
\documentclass{standalone}
\usepackage{circuitikz}
\begin{document}
\begin{circuitikz}[thick, node distance=2.5cm, scale=1]
    \draw
      (0,0) to[battery1, l_={\raisebox{-0.5cm}{\rotatebox{90}{$V_1 = %V1%\,\mathrm{V}$}}}] (0,-3)
      (3,-3) to[R, l={$R_1 = %R1%~\Omega$}] (0,-3)
      (3,-3) to[R, l_={$R_3 = %R3%~\Omega$}] (3,0)
      to[short] (0,0);

    \draw
      (3,0) to[short]
      (6,0) to[R, l={$R_2 = %R2%~\Omega$}] (6,-3)
      to[battery1, l={$V_2 = %V2%\,\mathrm{V}$}] (3,-3);

    % Current arrows (directions consistent with your checker)
    \draw[->] (1,0.3) -- (2,0.3);
    \node[above] at (1.5,0.3) {$I_1$};

    \draw[->] (4,0.3) -- (5,0.3);
    \node[above] at (4.5,0.3) {$I_2$};

    \draw[->] (2.6,-1) -- (2.6,-2);
    \node[left] at (2.6,-1.5) {$I_3$};
\end{circuitikz}
\end{document}
""".strip()


# -----------------------------
# Utilities
# -----------------------------
def run(cmd: list[str]) -> None:
    """Run a shell command with error surfacing."""
    subprocess.run(cmd, check=True)

def imagemagick_convert_cmd() -> list[str]:
    """
    Return the base command for ImageMagick convert.
    On some systems it's `magick convert`, on others just `convert`.
    WARNING: The convert command is deprecated in IMv7, use "magick" instead of "convert" or "magick convert"
    """
    # Try `magick convert` first
    try:
        subprocess.run(["magick", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # return ["magick", "convert"]
        return ["magick"]
    except Exception:
        # return ["convert"]
        return ["magick"]
        
def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

def load_problems() -> list[tuple[int, float, float, float, float, float]]:
    """
    Load problems.json and return a sorted list of (set_id, V1, V2, R1, R2, R3)
    """
    with open(PROBLEMS_JSON, "r") as f:
        data = json.load(f)
    items = []
    for k, vals in data.items():
        if not isinstance(vals, (list, tuple)) or len(vals) != 5:
            raise ValueError(f"Bad entry for key {k}: expected [V1,V2,R1,R2,R3]")
        set_id = int(k)
        V1, V2, R1, R2, R3 = map(float, vals)
        items.append((set_id, V1, V2, R1, R2, R3))
    # Sort by set id for stable output names
    items.sort(key=lambda x: x[0])
    return items


# -----------------------------
# Main build loop
# -----------------------------
def build_all():
    ensure_dirs()
    conv = imagemagick_convert_cmd()

    problems = load_problems()
    print(f"Generating {len(problems)} circuit diagrams...")

    for set_id, V1, V2, R1, R2, R3 in problems:
        # Prepare LaTeX content
        tex = (STANDALONE_TEX
               .replace("%V1%", f"{V1:g}")
               .replace("%V2%", f"{V2:g}")
               .replace("%R1%", f"{R1:g}")
               .replace("%R2%", f"{R2:g}")
               .replace("%R3%", f"{R3:g}"))

        tex_path = BUILD_DIR / f"circuit_set_{set_id}.tex"
        pdf_path = BUILD_DIR / f"circuit_set_{set_id}.pdf"
        cropped_pdf = BUILD_DIR / f"circuit_set_{set_id}_cropped.pdf"
        png_path = OUTPUT_DIR / f"circuit_set_{set_id}.png"

        tex_path.write_text(tex, encoding="utf-8")

        # Compile → PDF
        run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             "-output-directory", str(BUILD_DIR), str(tex_path)])

        # Crop → _cropped.pdf
        run(["pdfcrop", str(pdf_path), str(cropped_pdf)])

        # Convert → PNG
        run([*conv, "-density", DENSITY_DPI, str(cropped_pdf), "-quality", "100", str(png_path)])

        print(f"  ✓ Set {set_id:>2} → {png_path.name}")

    # Cleanup: delete everything except PNGs (we used BUILD_DIR, so just remove it)
    shutil.rmtree(BUILD_DIR, ignore_errors=True)
    print(f"\nDone. PNGs are in '{OUTPUT_DIR}'. Non-PNG build artifacts removed.")


if __name__ == "__main__":
    build_all()