"""
Generates customer arrival CSV files for restaurant queuing simulation.

This will create 200 CSV files in the scenarios/ directory
(100 lunch + 100 dinner, seeds 0..99) for reproducibility.

NOTE THAT ALTHOUGH WE GENERATED 200 CSV FILES, WE ENDED UP ON FOCUSING ON 100 LUNCH DATASETS INSTEAD
"""


import random
import csv
import math
import os


# groups per minute (1.57 customers/min / 2.61 avg party)
GROUP_ARRIVAL_RATE = 0.60

PARTY_SIZE_PROBS = [0.0416, 0.5836, 0.1740, 0.1457, 0.0379, 0.0171]

MAX_GROUP_SIZE = 6

DINING_DURATION = {
    "lunch":  {"mean": 44, "sd": 16},
    "dinner": {"mean": 50, "sd": 20},
}

MIN_DINING_DURATION = 10


def draw_exponential(rate, rng):
    """
    Draw from Exponential(rate) via inverse-transform: X = -ln(U) / rate.
    THIS CODE IS GENERATED FROM CLAUDE
    """
    u = rng.random()
    return -math.log(u) / rate


def draw_party_size(rng):
    """
    Draw a party size (1-6) from the empirical CDF.
    Result is capped at MAX_GROUP_SIZE (6).
    THIS CODE IS GENERATED FROM CLAUDE
    """
    u = rng.random()
    cumulative = 0.0
    for size, prob in enumerate(PARTY_SIZE_PROBS, start=1):
        cumulative += prob
        if u <= cumulative:
            return min(size, MAX_GROUP_SIZE)
    return MAX_GROUP_SIZE


def draw_dining_duration(meal_type, rng):
    """
    Draw a dining duration from Normal(mean, sd), clipped to MIN_DINING_DURATION.
    THIS CODE IS GENERATED FROM CLAUDE
    """
    params = DINING_DURATION[meal_type]
    duration = rng.gauss(params["mean"], params["sd"])
    duration = max(duration, MIN_DINING_DURATION)
    return round(duration)


# Main generation function

def generate_scenario(output_path, horizon=180, meal_type="lunch", seed=42):

    rng = random.Random(seed)

    # Generate inter-arrival times -> arrival times
    arrivals = []
    current_time = 0.0
    while True:
        inter_arrival = draw_exponential(GROUP_ARRIVAL_RATE, rng)
        current_time += inter_arrival
        if current_time > horizon:
            break
        arrivals.append(round(current_time, 1))

    # For each arrival draw group size (capped at 6) and dining duration
    rows = []
    for group_id, arrival_time in enumerate(arrivals, start=1):
        group_size = draw_party_size(rng)
        dining_duration = draw_dining_duration(meal_type, rng)
        rows.append({
            "group_id":        group_id,
            "arrival_time":    arrival_time,
            "group_size":      group_size,
            "dining_duration": dining_duration,
        })

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["group_id", "arrival_time",
                                               "group_size", "dining_duration"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    scenario_dir = os.path.join(os.path.dirname(__file__) or ".", "scenarios")
    NUM_SEEDS = 100
    seeds = list(range(NUM_SEEDS))

    print("Generating customer arrival scenarios (100 lunch + 100 dinner)...")
    print(f"  Group arrival rate : {GROUP_ARRIVAL_RATE} groups/min")
    print(f"  Simulation horizon : 180 minutes")
    print(f"  Max group size     : {MAX_GROUP_SIZE}")
    print(f"  Output directory   : {scenario_dir}")
    print()

    for meal in ("lunch", "dinner"):
        for seed in seeds:
            filename = f"{meal}_seed_{seed}.csv"
            filepath = os.path.join(scenario_dir, filename)
            n = generate_scenario(output_path=filepath, horizon=180,
                                  meal_type=meal, seed=seed)
            print(f"  {filename:<30s} -> {n:>3d} groups")

    print()
    print(f"Done. {2 * NUM_SEEDS} scenario files written to '{scenario_dir}'.")
