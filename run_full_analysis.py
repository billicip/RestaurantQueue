"""
run_full_analysis.py
====================
Master script that runs the complete analysis pipeline in order.

Steps:
  1. python generate_scenarios.py          -- regenerate all 200 scenario files
  2. python run_stage1_queue_comparison.py -- Stage 1: balanced tables
  3. python generate_data_driven_config.py -- Stage 2 & 3: distribution + config
  4. python run_stage4_data_driven_queue_comparison.py -- Stage 4: data-driven tables
  5. python compare_stage1_stage4.py       -- final comparison

Usage:
    python run_full_analysis.py
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Generate scenarios (100 lunch + 100 dinner)",
     [sys.executable, os.path.join(BASE_DIR, "generate_scenarios.py")]),
    ("Stage 1: Queue comparison — balanced 70-seat tables",
     [sys.executable, os.path.join(BASE_DIR, "run_stage1_queue_comparison.py")]),
    ("Stage 2 & 3: Group-size distribution + data-driven config",
     [sys.executable, os.path.join(BASE_DIR, "generate_data_driven_config.py")]),
    ("Stage 4: Queue comparison — data-driven 70-seat tables",
     [sys.executable, os.path.join(BASE_DIR, "run_stage4_data_driven_queue_comparison.py")]),
    ("Final comparison: Stage 1 vs Stage 4",
     [sys.executable, os.path.join(BASE_DIR, "compare_stage1_stage4.py")]),
]


def main():
    print("=" * 65)
    print("  Full Analysis Pipeline — COMP1110 Restaurant Queue Project")
    print("=" * 65)

    for i, (description, cmd) in enumerate(STEPS, 1):
        print(f"\n[Step {i}/{len(STEPS)}] {description}")
        print("-" * 65)
        result = subprocess.run(cmd, cwd=BASE_DIR)
        if result.returncode != 0:
            sys.exit(f"\nERROR: Step {i} failed with exit code {result.returncode}.")
        print(f"[Step {i}] Completed successfully.")

    print("\n" + "=" * 65)
    print("  All steps complete. Results are in the results/ directory.")
    print("=" * 65)


if __name__ == "__main__":
    main()
