"""
compare_stage1_stage4.py
========================
Read Stage 1 and Stage 4 summary CSVs and produce a final comparison.

Outputs:
    results/final_stage_comparison.csv

Usage:
    python compare_stage1_stage4.py
"""

import csv
import os
import sys

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

STAGE1_CSV = os.path.join(RESULTS_DIR, "stage1_queue_comparison_summary.csv")
STAGE4_CSV = os.path.join(RESULTS_DIR, "stage4_data_driven_queue_comparison_summary.csv")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "final_stage_comparison.csv")

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

DISCIPLINES = ["FCFS", "group_size", "priority"]


def load_summary(path):
    if not os.path.exists(path):
        sys.exit(f"ERROR: File not found: {path}\nRun the relevant stage script first.")
    data = {}
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            disc = row["discipline"]
            data[disc] = {m: float(row[m]) for m in METRICS}
    return data


def best_discipline(data, metric="average_waiting_time", lower_is_better=True):
    if lower_is_better:
        return min(data, key=lambda d: data[d][metric])
    return max(data, key=lambda d: data[d][metric])


def main():
    print("=" * 70)
    print("  Final Comparison: Stage 1 (Balanced) vs Stage 4 (Data-Driven)")
    print("=" * 70)

    s1 = load_summary(STAGE1_CSV)
    s4 = load_summary(STAGE4_CSV)

    best_s1 = best_discipline(s1)
    best_s4 = best_discipline(s4)

    print(f"\n  Best discipline under BALANCED tables   : {best_s1}")
    print(f"  Best discipline under DATA-DRIVEN tables: {best_s4}")

    print("\n  === Comparison by discipline ===")
    print(f"\n  {'Metric':<30} {'Stage':>7}", end="")
    for d in DISCIPLINES:
        print(f"  {d:>12}", end="")
    print()
    print(f"  {'-'*30} {'-'*7}", end="")
    for _ in DISCIPLINES:
        print(f"  {'-'*12}", end="")
    print()

    for m in METRICS:
        for stage_label, data in [("S1", s1), ("S4", s4)]:
            print(f"  {m:<30} {stage_label:>7}", end="")
            for d in DISCIPLINES:
                val = data.get(d, {}).get(m, float("nan"))
                print(f"  {val:>12.4f}", end="")
            print()
        # change row
        print(f"  {'  change':>37}", end="")
        for d in DISCIPLINES:
            v1 = s1.get(d, {}).get(m, 0)
            v4 = s4.get(d, {}).get(m, 0)
            delta = v4 - v1
            print(f"  {delta:>+12.4f}", end="")
        print()
        print()

    # --- Save comparison CSV ---
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = []
    for m in METRICS:
        for stage_label, data in [("Stage1_Balanced", s1), ("Stage4_DataDriven", s4)]:
            row = {"metric": m, "stage": stage_label}
            for d in DISCIPLINES:
                row[d] = round(data.get(d, {}).get(m, float("nan")), 4)
            rows.append(row)
        # delta row
        row = {"metric": m, "stage": "Delta(S4-S1)"}
        for d in DISCIPLINES:
            v1 = s1.get(d, {}).get(m, 0)
            v4 = s4.get(d, {}).get(m, 0)
            row[d] = round(v4 - v1, 4)
        rows.append(row)

    fieldnames = ["metric", "stage"] + DISCIPLINES
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Final comparison CSV -> {os.path.relpath(OUTPUT_CSV)}")

    # --- Conclusion summary ---
    avg_wait_metric = "average_waiting_time"
    served_metric   = "groups_served"
    within10_metric = "pct_seated_within_10min"
    util_metric     = "table_utilization"

    # Best discipline improvement in avg wait
    s1_best_wait = s1[best_s1][avg_wait_metric]
    s4_best_wait = s4[best_s4][avg_wait_metric]
    overall_delta = s4_best_wait - s1_best_wait

    # Average wait improvement across all disciplines
    s1_avg_all = sum(s1[d][avg_wait_metric] for d in DISCIPLINES) / 3
    s4_avg_all = sum(s4[d][avg_wait_metric] for d in DISCIPLINES) / 3
    avg_all_delta = s4_avg_all - s1_avg_all

    print("\n" + "=" * 70)
    print("  CONCLUSION SUMMARY")
    print("=" * 70)
    print(f"\n  Stage 1 best discipline : {best_s1}")
    print(f"    Mean avg waiting time : {s1_best_wait:.4f} min")
    print(f"\n  Stage 4 best discipline : {best_s4}")
    print(f"    Mean avg waiting time : {s4_best_wait:.4f} min")
    print(f"\n  Change in best avg wait (S4 − S1): {overall_delta:+.4f} min")
    print(f"  Change in mean avg wait across all disciplines: {avg_all_delta:+.4f} min")
    print()

    if avg_all_delta < -0.5:
        conclusion = ("The data-driven table configuration consistently reduces average "
                      "waiting time across all three queue disciplines. This suggests "
                      "that MATCHING TABLE SIZES TO CUSTOMER GROUP SIZES has a larger "
                      "impact on restaurant performance than the choice of queue discipline "
                      "alone. Table configuration appears to matter more than queue discipline.")
    elif avg_all_delta > 0.5:
        conclusion = ("The data-driven configuration did not improve average waiting time, "
                      "suggesting that the balanced layout already performs well for this "
                      "group-size distribution, or that queue discipline choice dominates.")
    else:
        conclusion = ("The performance difference between the balanced and data-driven "
                      "configurations is modest. Both table layout and queue discipline "
                      "contribute to overall restaurant performance.")

    print(f"  {conclusion}")
    print("=" * 70)


if __name__ == "__main__":
    main()
