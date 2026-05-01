# Restaurant Queue Simulation — COMP1110 Topic C

A discrete-event restaurant queue simulator built for COMP1110 Computing and Data Science in Everyday Life (HKU, Semester 2 2025-2026).

## Python Version

Python 3.8 or higher. No third-party packages required (standard library only).

## File Structure

```
├── simulator.py                               Core simulation engine
├── generate_scenarios.py                      Generates 200 scenario CSVs
├── generate_data_driven_config.py             Stage 2 & 3
├── run_stage1_queue_comparison.py             Stage 1
├── run_stage4_data_driven_queue_comparison.py Stage 4
├── compare_stage1_stage4.py                   Final comparison
├── run_full_analysis.py                       Master script
├── settings/  (balanced_70_*.json, data_driven_70_*.json, ...)
├── scenarios/ (lunch_seed_0..99.csv, dinner_seed_0..99.csv)
└── results/   (all output CSVs)
```

## Quickstart — Reproduce All Results

```bash
python run_full_analysis.py
```

## Step-by-step

```bash
python generate_scenarios.py
python run_stage1_queue_comparison.py
python generate_data_driven_config.py
python run_stage4_data_driven_queue_comparison.py
python compare_stage1_stage4.py
```

## Input Formats

Settings JSON: tables list (table_id, capacity), queues list, discipline ("fcfs"/"group_size"/"priority").
Scenario CSV: group_id, arrival_time, group_size, dining_duration.

## Key Output Files

| File                                                    | Description                               |
| ------------------------------------------------------- | ----------------------------------------- |
| results/group_size_distribution.csv                     | Stage 2 group-size counts and percentages |
| results/stage1_queue_comparison_summary.csv             | Stage 1 mean metrics                      |
| results/stage4_data_driven_queue_comparison_summary.csv | Stage 4 mean metrics                      |
| results/final_stage_comparison.csv                      | Side-by-side Stage 1 vs Stage 4           |

## Reproducibility

VIP seeds are fixed: `vip_seed = 1000 + scenario_seed`. Scenario files use seeds 0–99.
# RestaurantQueue
