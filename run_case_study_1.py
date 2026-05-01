"""
Case Study 1: Compare Queue Disciplines
=========================================
Compares three queue disciplines (FCFS, Group Size, Priority) using the same
table configuration (Config B balanced: 5x2 + 4x4 + 2x6 = 34 seats).

Runs 100 lunch scenarios (seeds 0-99) for each discipline and reports
averaged performance metrics across all 100 runs.

Assumptions applied (see simulator.py for full list):
  - Max group size: 6
  - Priority discipline: VIP membership via Bernoulli(p=0.05); VIP served
    first, FCFS within the same VIP tier.
  - Group size discipline: largest fitting group served first; FCFS on ties.
  - No table sharing between groups.
"""

import os
import sys
import json
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from generate_scenarios import generate_scenario
from simulator import run_simulation

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUM_SEEDS = 100
SEEDS     = list(range(NUM_SEEDS))

DISCIPLINE_SETTINGS = {
    "fcfs":       os.path.join(BASE_DIR, "settings", "baseline_fcfs.json"),
    "group_size": os.path.join(BASE_DIR, "settings", "baseline_group_size.json"),
    "priority":   os.path.join(BASE_DIR, "settings", "baseline_priority.json"),
}

SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
RESULTS_DIR   = os.path.join(BASE_DIR, "results")

METRICS = [
    "average_waiting_time",
    "max_waiting_time",
    "max_queue_length",
    "groups_served",
    "table_utilization",
    "pct_seated_within_10min",
    "vip_groups_total",
    "vip_avg_wait",
]


def ensure_dirs():
    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)


def generate_lunch_scenarios(seeds):
    """Generate lunch scenario files for each seed. Returns {seed: filepath}."""
    scenario_files = {}
    for seed in seeds:
        filename = f"lunch_seed_{seed}.csv"
        filepath = os.path.join(SCENARIOS_DIR, filename)
        generate_scenario(output_path=filepath, meal_type="lunch", seed=seed)
        scenario_files[seed] = filepath
    print(f"  Generated {len(seeds)} lunch scenarios.")
    return scenario_files


def run_all_simulations(scenario_files, discipline_settings):
    """Run every (discipline, seed) combination. Returns list of result dicts."""
    all_results = []
    total = len(discipline_settings) * len(scenario_files)
    done  = 0
    for discipline, settings_path in discipline_settings.items():
        for seed, scenario_path in scenario_files.items():
            result = run_simulation(
                settings_path=settings_path,
                scenario_path=scenario_path,
                vip_seed=seed,          # reproducible VIP draws per seed
            )
            result["discipline"] = discipline
            result["seed"]       = seed
            all_results.append(result)
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  Progress: {done}/{total} runs complete")
    return all_results


def compute_averages(all_results, disciplines):
    """Average each metric across seeds for each discipline."""
    averages = {}
    for discipline in disciplines:
        disc_results = [r for r in all_results if r["discipline"] == discipline]
        avg = {}
        for metric in METRICS:
            values     = [r[metric] for r in disc_results]
            avg[metric] = sum(values) / len(values) if values else 0.0
        averages[discipline] = avg
    return averages


def print_comparison_table(averages):
    disciplines   = list(averages.keys())
    metric_width  = 26
    col_width     = 14

    header = f"{'Metric':<{metric_width}}"
    for d in disciplines:
        header += f"{d:>{col_width}}"

    print("\n" + "=" * len(header))
    print(f"CASE STUDY 1: Queue Discipline Comparison (averaged over {NUM_SEEDS} seeds)")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for metric in METRICS:
        row = f"{metric:<{metric_width}}"
        for d in disciplines:
            val = averages[d][metric]
            if metric in ("table_utilization", "pct_seated_within_10min"):
                row += f"{val * 100 if val <= 1 else val:>{col_width - 1}.1f}%"
            else:
                row += f"{val:>{col_width}.2f}"
        print(row)

    print("-" * len(header))


def save_results_csv(all_results, filepath):
    fieldnames = ["discipline", "seed"] + METRICS
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
    print(f"\nResults saved to: {filepath}")


def determine_best_discipline(averages):
    best, best_val = None, float("inf")
    for discipline, metrics in averages.items():
        if metrics["average_waiting_time"] < best_val:
            best_val = metrics["average_waiting_time"]
            best     = discipline
    return best, best_val


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ensure_dirs()

    print(f"Step 1: Generating {NUM_SEEDS} lunch scenarios...")
    scenario_files = generate_lunch_scenarios(SEEDS)

    print(f"\nStep 2: Running simulations ({NUM_SEEDS * len(DISCIPLINE_SETTINGS)} total)...")
    all_results = run_all_simulations(scenario_files, DISCIPLINE_SETTINGS)

    print("\nStep 3: Computing averages and comparing...")
    disciplines = list(DISCIPLINE_SETTINGS.keys())
    averages    = compute_averages(all_results, disciplines)

    print_comparison_table(averages)

    csv_path = os.path.join(RESULTS_DIR, "case_study_1_results.csv")
    save_results_csv(all_results, csv_path)

    best, best_val = determine_best_discipline(averages)
    print(f"\n*** Best discipline: {best} (avg wait = {best_val:.2f} min) ***\n")
    return best


if __name__ == "__main__":
    best_discipline = main()
