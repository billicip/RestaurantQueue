"""
generate_data_driven_config.py
==============================
Stage 2: Analyse group-size distribution across 100 lunch datasets.
Stage 3: Generate a data-driven 70-seat table configuration and save
         three settings files (FCFS / group_size / priority).

Usage:
    python generate_data_driven_config.py

Outputs:
    results/group_size_distribution.csv
    settings/data_driven_70_fcfs.json
    settings/data_driven_70_group_size.json
    settings/data_driven_70_priority.json
"""

import csv
import json
import os
from collections import Counter

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(BASE_DIR, "scenarios")
SETTINGS_DIR  = os.path.join(BASE_DIR, "settings")
RESULTS_DIR   = os.path.join(BASE_DIR, "results")
NUM_SEEDS     = 100
TOTAL_SEATS   = 70

# ---------------------------------------------------------------------------
# Stage 2: Count group sizes across all 100 lunch datasets
# ---------------------------------------------------------------------------

def count_group_sizes():
    counts = Counter()
    for seed in range(NUM_SEEDS):
        path = os.path.join(SCENARIOS_DIR, f"lunch_seed_{seed}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Missing scenario file: {path}\n"
                "Run python generate_scenarios.py first."
            )
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                size = int(row["group_size"])
                counts[size] += 1
    return counts


def compute_percentages(counts):
    total = sum(counts.values())
    return {size: counts[size] / total * 100 for size in sorted(counts)}


# ---------------------------------------------------------------------------
# Stage 3: Map percentages -> table demand -> table configuration
# ---------------------------------------------------------------------------

def map_to_table_demand(percentages):
    """
    Groups 1-2  -> demand for 2-seat tables
    Groups 3-4  -> demand for 4-seat tables
    Groups 5-6  -> demand for 6-seat tables
    Returns dict {2: pct, 4: pct, 6: pct} that sums to 100.
    """
    demand = {
        2: percentages.get(1, 0) + percentages.get(2, 0),
        4: percentages.get(3, 0) + percentages.get(4, 0),
        6: percentages.get(5, 0) + percentages.get(6, 0),
    }
    return demand


def design_tables(demand, total_seats=TOTAL_SEATS):
    """
    Allocate seats to table types proportionally to demand,
    then convert seat counts to table counts, rounding to integers
    while keeping the total exactly equal to total_seats.

    Algorithm:
      1. Compute ideal seat allocation per type (proportional to demand).
      2. Compute ideal number of tables = ideal_seats / capacity.
      3. Round each down to integer tables -> each contributes capacity*n seats.
      4. Distribute remaining seats greedily (largest remainder first).
      5. Guarantee at least one table of each type for coverage.

    Returns dict {capacity: n_tables}.
    """
    capacities = [2, 4, 6]
    total_demand = sum(demand.values())

    # Step 1 — ideal seats per type
    ideal_seats = {cap: demand[cap] / total_demand * total_seats
                   for cap in capacities}

    # Step 2 — ideal tables per type (fractional)
    ideal_tables = {cap: ideal_seats[cap] / cap for cap in capacities}

    # Step 3 — floor tables and count used seats
    n_tables = {cap: max(1, int(ideal_tables[cap])) for cap in capacities}
    used_seats = sum(cap * n_tables[cap] for cap in capacities)
    remaining = total_seats - used_seats

    # Step 4 — distribute remaining seats by largest-remainder approach
    # Compute fractional parts of ideal_tables adjusted for floor already taken
    remainders = {}
    for cap in capacities:
        actual_floor = n_tables[cap]
        remainders[cap] = ideal_tables[cap] - actual_floor

    # Keep adding one table of the type with most remainder until seats filled
    while remaining != 0:
        if remaining > 0:
            # Add one table of the type with largest fractional remainder
            best_cap = max(capacities, key=lambda c: (remainders[c], -c))
            if best_cap <= remaining:
                n_tables[best_cap] += 1
                used_seats += best_cap
                remaining -= best_cap
                remainders[best_cap] -= 1.0  # consumed this remainder
            else:
                # Best cap too big; try smaller
                placed = False
                for cap in sorted(capacities):
                    if cap <= remaining:
                        n_tables[cap] += 1
                        remaining -= cap
                        placed = True
                        break
                if not placed:
                    break   # cannot place further (shouldn't happen with cap>=2)
        else:
            # Remove one table of the type with smallest fractional remainder
            worst_cap = min(capacities, key=lambda c: (remainders[c], n_tables[c]))
            if n_tables[worst_cap] > 1:
                n_tables[worst_cap] -= 1
                remaining += worst_cap
                remainders[worst_cap] += 1.0

    # Final check
    actual_total = sum(cap * n for cap, n in n_tables.items())
    assert actual_total == total_seats, (
        f"Seat count mismatch: expected {total_seats}, got {actual_total}"
    )
    return n_tables


def build_tables_list(n_tables):
    """Convert {capacity: count} to the list of table dicts expected by simulator."""
    tables = []
    tid = 1
    for cap in sorted(n_tables):
        for _ in range(n_tables[cap]):
            tables.append({"table_id": f"T{tid}", "capacity": cap})
            tid += 1
    return tables


def save_settings(tables, discipline, filepath, description):
    """Save a settings JSON file."""
    if discipline == "group_size":
        queues = [
            {"queue_id": "Q1", "min_size": 1, "max_size": 2},
            {"queue_id": "Q2", "min_size": 3, "max_size": 4},
            {"queue_id": "Q3", "min_size": 5, "max_size": 6},
        ]
    else:
        queues = [{"queue_id": "Q_MAIN", "min_size": 1, "max_size": 6}]

    obj = {
        "description": description,
        "tables": tables,
        "queues": queues,
        "discipline": discipline,
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"  Saved: {os.path.relpath(filepath)}")


def save_group_size_distribution(counts, percentages, demand):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "group_size_distribution.csv")
    total = sum(counts.values())
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["group_size", "count", "percentage",
                         "table_type_mapped", "table_demand_pct"])
        for size in sorted(counts):
            cap = 2 if size <= 2 else (4 if size <= 4 else 6)
            writer.writerow([
                size,
                counts[size],
                f"{percentages[size]:.2f}",
                cap,
                f"{demand[cap]:.2f}",
            ])
        writer.writerow(["TOTAL", total, "100.00", "", ""])
    print(f"  Saved: results/group_size_distribution.csv")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Stage 2: Group-Size Distribution Analysis")
    print("=" * 60)

    counts = count_group_sizes()
    percentages = compute_percentages(counts)
    total_groups = sum(counts.values())

    print(f"\n  Scanned {NUM_SEEDS} lunch scenario files.")
    print(f"  Total groups analysed: {total_groups}\n")
    print(f"  {'Size':>6}  {'Count':>8}  {'Percentage':>12}")
    print(f"  {'------':>6}  {'--------':>8}  {'----------':>12}")
    for size in sorted(counts):
        print(f"  {size:>6}  {counts[size]:>8}  {percentages[size]:>11.2f}%")

    print()
    print("=" * 60)
    print("  Stage 3: Data-Driven Table Configuration Design")
    print("=" * 60)

    demand = map_to_table_demand(percentages)
    print(f"\n  Table-demand percentages (mapped from group sizes):")
    print(f"    2-seat tables (groups 1-2): {demand[2]:.2f}%")
    print(f"    4-seat tables (groups 3-4): {demand[4]:.2f}%")
    print(f"    6-seat tables (groups 5-6): {demand[6]:.2f}%")

    n_tables = design_tables(demand, TOTAL_SEATS)
    total_seats = sum(cap * n for cap, n in n_tables.items())

    print(f"\n  Generated data-driven 70-seat table configuration:")
    for cap in sorted(n_tables):
        print(f"    {n_tables[cap]} tables of capacity {cap}"
              f" = {n_tables[cap] * cap} seats")
    print(f"    Total seats: {total_seats}")
    assert total_seats == TOTAL_SEATS

    tables_list = build_tables_list(n_tables)

    # Save group-size distribution CSV
    save_group_size_distribution(counts, percentages, demand)

    # Save the three data-driven settings files
    print()
    configs = [
        ("fcfs",       "data_driven_70_fcfs.json",
         "Stage 4 Data-Driven 70-seat layout — FCFS discipline."),
        ("group_size", "data_driven_70_group_size.json",
         "Stage 4 Data-Driven 70-seat layout — group_size discipline."),
        ("priority",   "data_driven_70_priority.json",
         "Stage 4 Data-Driven 70-seat layout — priority discipline."),
    ]
    for discipline, filename, desc in configs:
        filepath = os.path.join(SETTINGS_DIR, filename)
        save_settings(tables_list, discipline, filepath, desc)

    print("\nDone. Stage 2 and Stage 3 complete.")


if __name__ == "__main__":
    main()
