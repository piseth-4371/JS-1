"""Test and run every short-plan day in ONE command (from the backend folder):

    .\\.venv\\Scripts\\python learning\\run_all.py

1. Runs the checks for days 3, 4, 7, 8, 14 and 15.
2. If they all pass, runs each day's script so you see its answer on real data.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAYS = [("3", "ch03_expected_value"), ("4", "ch04_random_walk"), ("7", "ch07_volatility"),
        ("8", "ch08_sharpe"), ("14", "ch14_kelly"), ("15", "ch15_monte_carlo")]


def main() -> int:
    checks = [str(HERE / f"check_{name.split('_')[0]}.py") for _, name in DAYS]
    print("=== Checks for days " + ", ".join(d for d, _ in DAYS) + " ===")
    if subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *checks]).returncode:
        print("\nSome checks failed (see above). Fix them first; no scripts were run.")
        return 1
    for day, name in DAYS:
        print(f"\n=== Day {day}: {name} ===")
        subprocess.run([sys.executable, str(HERE / f"{name}.py")], check=True)
    print("\nAll 6 days of the short plan pass. You are finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
