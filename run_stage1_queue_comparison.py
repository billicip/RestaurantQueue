"""
run_stage1_queue_comparison.py
==============================
Stage 1: Compare three queue disciplines (FCFS, group_size, priority)
using the balanced 70-seat table configuration across 100 lunch datasets.

Outputs:
    results/stage1_queue_comparison_detailed.csv
    results/stage1_queue_comparison_summary.csv

Usage:
    python run_stage1_queue_comparison.py
"""

from simulator import run_simulation
import csv
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_SEEDS = 100
# fixed base seed for reproducibility; actual seed = base + scenario_seed
VIP_BASE_SEED = 1000

SETTINGS = [
    ("FCFS",       os.path.join(BASE_DIR, "settings", "balanced_70_fcfs.json")),
    ("group_size", os.path.join(BASE_DIR, "settings", "balanced_70_group_size.json")),
    ("priority",   os.path.join(BASE_DIR, "settings", "balanced_70_priority.json")),
]

SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

DETAILED_CSV = os.path.join(
    RESULTS_DIR, "stage1_queue_comparison_detailed.csv")
SUMMARY_CSV = os.path.join(RESULTS_DIR, "stage1_queue_comparison_summary.csv")

METRICS = [
    "average_waiting_time",
    "max_waiting_time",
    "max_queue_length",
    "groups_served",
    "groups_not_served",
    "table_utilization",
    "pct_seated_within_10min",
    "vip_groups_total",
    "vip_avg_wait",
]


# Helpers

def check_files():
    for label, path in SETTINGS:
        if not os.path.exists(path):
            sys.exit(f"ERROR: Settings file not found: {path}")
    for seed in range(NUM_SEEDS):
        p = os.path.join(SCENARIOS_DIR, f"lunch_seed_{seed}.csv")
        if not os.path.exists(p):
            sys.exit(f"ERROR: Scenario file not found: {p}\n"
                     "Run python generate_scenarios.py first.")


def mean(values):
    return sum(values) / len(values) if values else 0.0


# Main

def main():
    print("=" * 65)
    print("  Stage 1: Queue Discipline Comparison — Balanced 70-seat Tables")
    print("=" * 65)

    check_files()
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_rows = []

    for label, settings_path in SETTINGS:
        print(f"\n  Running discipline: {label} ...")
        for seed in range(NUM_SEEDS):
            scenario_path = os.path.join(
                SCENARIOS_DIR, f"lunch_seed_{seed}.csv")
            vip_seed = VIP_BASE_SEED + seed
            metrics = run_simulation(
                settings_path, scenario_path, vip_seed=vip_seed)
            row = {"discipline": label, "seed": seed}
            row.update(metrics)
            all_rows.append(row)
        print(f"    Completed {NUM_SEEDS} runs.")

    # Write detailed CSV
    fieldnames = ["discipline", "seed"] + METRICS
    with open(DETAILED_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\n  Detailed results -> {os.path.relpath(DETAILED_CSV)}")

    # Compute summaries
    summaries = {}
    for label, _ in SETTINGS:
        rows = [r for r in all_rows if r["discipline"] == label]
        summaries[label] = {m: mean([r[m] for r in rows]) for m in METRICS}

    # Write summary CSV
    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["discipline"] + METRICS)
        writer.writeheader()
        for label in [l for l, _ in SETTINGS]:
            row = {"discipline": label}
            row.update({m: round(summaries[label][m], 4) for m in METRICS})
            writer.writerow(row)
    print(f"  Summary results  -> {os.path.relpath(SUMMARY_CSV)}")

    # Print results table
    print("\n" + "=" * 65)
    print("  Stage 1 Mean Results (across 100 lunch datasets)")
    print("=" * 65)
    print(f"  {'Metric':<30} {'FCFS':>12} {'group_size':>12} {'priority':>12}")
    print(f"  {'-'*30} {'-'*12} {'-'*12} {'-'*12}")
    for m in METRICS:
        vals = [summaries[l][m] for l, _ in SETTINGS]
        print(f"  {m:<30} {vals[0]:>12.4f} {vals[1]:>12.4f} {vals[2]:>12.4f}")

    # Identify best discipline by lowest average waiting time
    best_label = min(
        summaries, key=lambda l: summaries[l]["average_waiting_time"])
    print(f"\n  Best queue discipline (lowest avg wait): {best_label}")
    print(
        f"  Average waiting time: {summaries[best_label]['average_waiting_time']:.4f} min")
    print("=" * 65)


if __name__ == "__main__":
    main()
