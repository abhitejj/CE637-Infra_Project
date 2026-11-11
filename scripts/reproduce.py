#!/usr/bin/env python3
"""Rebuild baseline artifacts and run checks with a complete combined terminal log."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    os.chdir(ROOT)
    logs = ROOT / "outputs" / "audit"
    logs.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("MPLCONFIGDIR", "/private/tmp/grain-mpl")
    env.setdefault("XDG_CACHE_HOME", "/private/tmp/grain-cache")
    commands = [(ROOT, [sys.executable, f"scripts/{name}"]) for name in (
        "01_build_dataset.py", "02_generate_input_tables.py", "03_solve_optimization.py",
        "04_sensitivity_analysis.py", "05_generate_figures.py")]
    latex = shutil.which("pdflatex") or "/Library/TeX/texbin/pdflatex"
    if not Path(latex).exists():
        raise RuntimeError("pdflatex is required to reproduce the PDF deliverables")
    for name in ("Summary_Slide.tex", "Final_Report.tex", "Poster.tex"):
        commands.append((ROOT / "report", [latex, "-halt-on-error", "-interaction=nonstopmode", name]))
    commands.append((ROOT, [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]))
    with (logs / "reproduction.log").open("w") as log:
        for cwd, command in commands:
            header = f"\nRUN {command!r} (cwd={cwd})\n"
            print(header, end="", flush=True)
            log.write(header)
            log.flush()
            process = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
            code = process.wait()
            log.write(f"EXIT {code}\n")
            log.flush()
            if code:
                raise RuntimeError(f"Command failed ({code}); see {logs / 'reproduction.log'}")
    print(f"Reproduction completed; full terminal evidence: {logs / 'reproduction.log'}")


if __name__ == "__main__":
    main()
