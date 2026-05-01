
from simulator import run_simulation
from generate_scenarios import generate_scenario
import os
import sys
import json
import csv
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


NUM_SEEDS = 100
SEEDS = list(range(NUM_SEEDS))
SCENARIO_TYPES = ["lunch", "dinner"]

CONFIG_FILES = {
    "config_a_small_heavy": os.path.join(BASE_DIR, "settings", "config_a_small_heavy.json"),
    "config_b_balanced":    os.path.join(BASE_DIR, "settings", "config_b_balanced.json"),
    "config_c_large_heavy": os.path.join(BASE_DIR, "settings", "config_c_large_heavy.json"),
}

SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

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


def get_queues_for_discipline(discipline):
    if discipline == "group_size":
        return [
            {"queue_id": "Q1", "min_size": 1, "max_size": 2},
            {"queue_id": "Q2", "min_size": 3, "max_size": 4},
            {"queue_id": "Q3", "min_size": 5, "max_size": 6},
        ]
    else:
        return [{"queue_id": "Q1", "min_size": 1, "max_size": 6}]


def update_settings_files(discipline):
    """Update all Case Study 2 settings files with the chosen discipline."""
    queues = get_queues_for_discipline(discipline)
    for config_name, filepath in CONFIG_FILES.items():
        with open(filepath, "r") as f:
            settings = json.load(f)
        settings["discipline"] = discipline
        settings["queues"] = queues
        with open(filepath, "w") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
    print(
        f"  Updated {len(CONFIG_FILES)} config files -> discipline='{discipline}'")


def generate_scenarios(seeds, scenario_types):
    """Generate scenario files. Returns {(type, seed): filepath}."""
    scenario_files = {}
    for stype in scenario_types:
        for seed in seeds:
            filename = f"{stype}_seed_{seed}.csv"
            filepath = os.path.join(SCENARIOS_DIR, filename)
            generate_scenario(output_path=filepath, meal_type=stype, seed=seed)
            scenario_files[(stype, seed)] = filepath
    print(f"  Generated {len(scenario_files)} scenario files "
          f"({len(seeds)} seeds x {len(scenario_types)} types).")
    return scenario_files


def run_all_simulations(scenario_files, config_files):
    """Run every (config, scenario_type, seed) combination."""
    all_results = []
    total = len(config_files) * len(scenario_files)
    done = 0
    for config_name, settings_path in config_files.items():
        for (stype, seed), scenario_path in scenario_files.items():
            result = run_simulation(
                settings_path=settings_path,
                scenario_path=scenario_path,
                vip_seed=seed,
            )
            result["config"] = config_name
            result["scenario_type"] = stype
            result["seed"] = seed
            all_results.append(result)
            done += 1
            if done % 100 == 0 or done == total:
                print(f"  Progress: {done}/{total} runs complete")
    return all_results


def compute_averages(all_results, configs, scenario_type):
    """Average each metric across seeds for each config, filtered by scenario_type."""
    averages = {}
    for config in configs:
        filtered = [r for r in all_results
                    if r["config"] == config and r["scenario_type"] == scenario_type]
        avg = {}
        for metric in METRICS:
            values = [r[metric] for r in filtered]
            avg[metric] = sum(values) / len(values) if values else 0.0
        averages[config] = avg
    return averages


def print_comparison_table(averages, scenario_type):
    configs = list(averages.keys())
    display_names = {
        "config_a_small_heavy": "A (small)",
        "config_b_balanced":    "B (balanced)",
        "config_c_large_heavy": "C (large)",
    }
    metric_width = 26
    col_width = 16

    header = f"{'Metric':<{metric_width}}"
    for c in configs:
        header += f"{display_names.get(c, c):>{col_width}}"

    print("\n" + "=" * len(header))
    print(f"CASE STUDY 2: Table Config Comparison - {scenario_type.upper()} "
          f"(averaged over {NUM_SEEDS} seeds)")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for metric in METRICS:
        row = f"{metric:<{metric_width}}"
        for c in configs:
            val = averages[c][metric]
            if metric in ("table_utilization", "pct_seated_within_10min"):
                row += f"{val * 100 if val <= 1 else val:>{col_width - 1}.1f}%"
            else:
                row += f"{val:>{col_width}.2f}"
        print(row)

    print("-" * len(header))


def save_results_csv(all_results, filepath):
    fieldnames = ["config", "scenario_type", "seed"] + METRICS
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_results:
            writer.writerow(row)
    print(f"\nResults saved to: {filepath}")


def determine_best_config(all_results, configs):
    best, best_val = None, float("inf")
    for config in configs:
        filtered = [r for r in all_results if r["config"] == config]
        if not filtered:
            continue
        avg_wait = sum(r["average_waiting_time"]
                       for r in filtered) / len(filtered)
        if avg_wait < best_val:
            best_val = avg_wait
            best = config
    return best, best_val


# Main

def main():
    parser = argparse.ArgumentParser(
        description="Case Study 2: Compare table configurations using the best discipline."
    )
    parser.add_argument(
        "--discipline", type=str, default="fcfs",
        choices=["fcfs", "group_size", "priority"],
        help="Best discipline from Case Study 1 (default: fcfs)",
    )
    args = parser.parse_args()
    discipline = args.discipline

    ensure_dirs()
    print(f"Using discipline: '{discipline}'\n")

    print("Step 1: Updating settings files with chosen discipline...")
    update_settings_files(discipline)

    print(f"\nStep 2: Generating scenarios ({NUM_SEEDS} seeds x 2 types)...")
    scenario_files = generate_scenarios(SEEDS, SCENARIO_TYPES)

    total_runs = len(CONFIG_FILES) * len(scenario_files)
    print(f"\nStep 3: Running simulations ({total_runs} total)...")
    all_results = run_all_simulations(scenario_files, CONFIG_FILES)

    print("\nStep 4: Computing averages and comparing...")
    configs = list(CONFIG_FILES.keys())
    for stype in SCENARIO_TYPES:
        averages = compute_averages(all_results, configs, stype)
        print_comparison_table(averages, stype)

    csv_path = os.path.join(RESULTS_DIR, "case_study_2_results.csv")
    save_results_csv(all_results, csv_path)

    best, best_val = determine_best_config(all_results, configs)
    print(f"\n*** Best configuration: {best} "
          f"(overall avg wait = {best_val:.2f} min) ***\n")
    return best


if __name__ == "__main__":
    best_config = main()
