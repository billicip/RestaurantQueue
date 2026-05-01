

import csv
import heapq
import json
import random
import sys
from collections import OrderedDict


def load_settings(path):

    with open(path, "r") as f:
        return json.load(f)


def load_arrivals(path):
    """
        Read the customer arrival CSV file.
    """
    arrivals = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            group_size = min(int(row["group_size"]), 6)  # max group size = 6
            arrivals.append({
                "group_id":        row["group_id"],
                "arrival_time":    float(row["arrival_time"]),
                "group_size":      group_size,
                "dining_duration": float(row["dining_duration"]),
            })
    return arrivals


def assign_vip_flags(arrivals, vip_prob=0.05, seed=None):
    """
    Assign a VIP flag to each group using an independent Bernoulli draw.

    """
    rng = random.Random(seed)
    for group in arrivals:
        group["is_vip"] = (rng.random() < vip_prob)
    return arrivals


------

_event_counter = 0  # module-level counter for tie-breaking


def make_event(time, event_type, data):
    """Create an event tuple that can be pushed onto the heapq."""
    global _event_counter
    _event_counter += 1
    return (time, _event_counter, event_type, data)


def find_best_table(tables_free, group_size):
    """
    Find the smallest free table that can fit `group_size` people.
    No table sharing: capacity must be >= group_size.

    Returns the table_id of the best fit, or None if nothing fits.
    """
    best_id = None
    best_cap = float("inf")

    for tid, cap in tables_free.items():
        if cap >= group_size and cap < best_cap:
            best_cap = cap
            best_id = tid

    return best_id


def route_to_queue(group, queues_config):
    """
    For the 'group_size' discipline, decide which queue a group belongs to.
    Returns the queue_id string.
    """
    size = group["group_size"]
    for q in queues_config:
        if q["min_size"] <= size <= q["max_size"]:
            return q["queue_id"]
    return queues_config[0]["queue_id"]


def pick_next_fcfs(queues):
    """
    FCFS discipline: single queue keyed "Q_MAIN".
    Pop and return the front group, or None if empty.
    """
    q = queues.get("Q_MAIN", [])
    if q:
        return q.pop(0)
    return None


def pick_next_group_size(queues, tables_free):
    """
    group_size discipline: serve the LARGEST group that fits a free table.
    Within ties on size, use FCFS (earliest arrival_time).
    No table sharing -- a table must have capacity >= group_size.

    Checks only the FRONT of each sub-queue (FCFS ordering within each queue).
    Returns the chosen group (removed from its queue), or None.
    """
    best_qid = None
    best_group = None
    best_size = -1
    best_arrival = float("inf")

    for qid, q in queues.items():
        if not q:
            continue
        front = q[0]
        size = front["group_size"]
        if find_best_table(tables_free, size) is None:
            continue
        # Prefer LARGEST group; break ties by FCFS
        if (size > best_size) or (size == best_size and front["arrival_time"] < best_arrival):
            best_size = size
            best_arrival = front["arrival_time"]
            best_qid = qid
            best_group = front

    if best_qid is not None:
        queues[best_qid].pop(0)
        return best_group
    return None


def pick_next_priority(queues, tables_free):
    """
    priority discipline: single queue keyed "Q_MAIN".

    VIP groups (is_vip=True, ~5% Bernoulli) are always served before
    non-VIP groups.  Within the same VIP tier, FCFS (earliest arrival)
    is used.  Only groups that fit an available table are considered.
    """
    q = queues.get("Q_MAIN", [])
    best_idx = None
    best_arrival = float("inf")
    best_is_vip = False

    for i, group in enumerate(q):
        if find_best_table(tables_free, group["group_size"]) is None:
            continue

        is_vip = group.get("is_vip", False)
        arrival = group["arrival_time"]

        if best_idx is None:
            selected = True
        elif is_vip and not best_is_vip:
            selected = True          # VIP beats non-VIP unconditionally
        elif not is_vip and best_is_vip:
            selected = False         # non-VIP cannot beat VIP
        else:
            selected = (arrival < best_arrival)   # same tier -> FCFS

        if selected:
            best_idx = i
            best_arrival = arrival
            best_is_vip = is_vip

    if best_idx is not None:
        return q.pop(best_idx)
    return None


def run_simulation(settings_path, scenario_path, vip_seed=None):
    """
    Run the discrete-event simulation and return a dict of metrics.
    """

    global _event_counter
    _event_counter = 0

    SIM_HORIZON = 180.0   # hard simulation stop (minutes)

    settings = load_settings(settings_path)
    arrivals = load_arrivals(scenario_path)
    discipline = settings.get("discipline", "fcfs")
    tables_config = settings["tables"]
    queues_config = settings.get("queues", [{"queue_id": "Q_MAIN",
                                             "min_size": 1, "max_size": 6}])

    assign_vip_flags(arrivals, vip_prob=0.05, seed=vip_seed)

    tables_free = OrderedDict()
    tables_all = OrderedDict()
    for t in tables_config:
        tables_free[t["table_id"]] = t["capacity"]
        tables_all[t["table_id"]] = t["capacity"]

    queues = {}
    if discipline == "group_size":
        for q in queues_config:
            queues[q["queue_id"]] = []
    else:
        queues["Q_MAIN"] = []

    event_heap = []
    for a in arrivals:
        if a["arrival_time"] <= SIM_HORIZON:
            heapq.heappush(event_heap, make_event(
                a["arrival_time"], "ARRIVAL", a))

    waiting_times = []
    vip_wait_times = []
    max_queue_len = 0
    groups_served = 0
    busy_intervals = {tid: [] for tid in tables_all}

    def total_queue_length():
        return sum(len(q) for q in queues.values())

    def try_seat_from_queue(current_time):
        nonlocal max_queue_len, groups_served
        while True:
            if discipline == "fcfs":
                group = pick_next_fcfs(queues)
            elif discipline == "group_size":
                group = pick_next_group_size(queues, tables_free)
            elif discipline == "priority":
                group = pick_next_priority(queues, tables_free)
            else:
                group = None

            if group is None:
                break

            table_id = find_best_table(tables_free, group["group_size"])
            if table_id is None:
                # Safety: put group back at front
                if discipline == "group_size":
                    qid = route_to_queue(group, queues_config)
                    queues[qid].insert(0, group)
                else:
                    queues["Q_MAIN"].insert(0, group)
                break

            del tables_free[table_id]
            wait = current_time - group["arrival_time"]
            waiting_times.append(wait)
            if group.get("is_vip", False):
                vip_wait_times.append(wait)
            groups_served += 1

            depart_time = current_time + group["dining_duration"]
            busy_intervals[table_id].append((current_time, depart_time))

            heapq.heappush(event_heap, make_event(depart_time, "DEPARTURE", {
                "table_id": table_id,
                "group_id": group["group_id"],
            }))

    last_event_time = 0.0

    while event_heap:
        time, _tie, etype, data = heapq.heappop(event_heap)

        if time > SIM_HORIZON:
            break

        last_event_time = time

        if etype == "ARRIVAL":
            group = data
            table_id = find_best_table(tables_free, group["group_size"])

            if table_id is not None:
                del tables_free[table_id]
                waiting_times.append(0.0)
                if group.get("is_vip", False):
                    vip_wait_times.append(0.0)
                groups_served += 1

                depart_time = time + group["dining_duration"]
                busy_intervals[table_id].append((time, depart_time))

                heapq.heappush(event_heap, make_event(depart_time, "DEPARTURE", {
                    "table_id": table_id,
                    "group_id": group["group_id"],
                }))
            else:
                if discipline == "group_size":
                    qid = route_to_queue(group, queues_config)
                    queues[qid].append(group)
                else:
                    queues["Q_MAIN"].append(group)

                qlen = total_queue_length()
                if qlen > max_queue_len:
                    max_queue_len = qlen

        elif etype == "DEPARTURE":
            table_id = data["table_id"]
            tables_free[table_id] = tables_all[table_id]

            try_seat_from_queue(time)

            qlen = total_queue_length()
            if qlen > max_queue_len:
                max_queue_len = qlen

    groups_not_served = total_queue_length()

    if waiting_times:
        avg_wait = sum(waiting_times) / len(waiting_times)
        max_wait = max(waiting_times)
        pct_within_10 = (sum(1 for w in waiting_times if w <= 10.0)
                         / len(waiting_times)) * 100.0
    else:
        avg_wait = max_wait = pct_within_10 = 0.0

    vip_avg_wait = (sum(vip_wait_times) / len(vip_wait_times)
                    if vip_wait_times else 0.0)

    horizon = min(last_event_time, SIM_HORIZON) if last_event_time > 0 else 1.0
    total_busy = 0.0
    total_possible = 0.0
    for tid in tables_all:
        total_possible += horizon
        for (start, end) in busy_intervals[tid]:
            total_busy += min(end, horizon) - start

    utilization = total_busy / total_possible if total_possible > 0 else 0.0

    return {
        "average_waiting_time":    round(avg_wait, 2),
        "max_waiting_time":        round(max_wait, 2),
        "max_queue_length":        max_queue_len,
        "groups_served":           groups_served,
        "groups_not_served":       groups_not_served,
        "table_utilization":       round(utilization, 4),
        "pct_seated_within_10min": round(pct_within_10, 2),
        "vip_groups_total":        len(vip_wait_times),
        "vip_avg_wait":            round(vip_avg_wait, 2),
    }


# ---------------------------------------------------------------------------
# 9. COMMAND-LINE INTERFACE
# ---------------------------------------------------------------------------

def print_metrics(metrics):
    """Pretty-print the simulation results."""
    print("=" * 50)
    print("  RESTAURANT QUEUE SIMULATION RESULTS")
    print("=" * 50)
    print(f"  Groups served:             {metrics['groups_served']}")
    print(f"  Groups not served (left):  {metrics['groups_not_served']}")
    print(
        f"  Average waiting time:      {metrics['average_waiting_time']:.2f} min")
    print(
        f"  Max waiting time:          {metrics['max_waiting_time']:.2f} min")
    print(f"  Max queue length:          {metrics['max_queue_length']}")
    print(
        f"  Table utilization:         {metrics['table_utilization'] * 100:.2f}%")
    print(
        f"  Seated within 10 min:      {metrics['pct_seated_within_10min']:.2f}%")
    print(f"  VIP groups (total):        {metrics['vip_groups_total']}")
    print(f"  VIP average wait:          {metrics['vip_avg_wait']:.2f} min")
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python simulator.py <settings.json> <arrivals.csv>")
        sys.exit(1)

    results = run_simulation(sys.argv[1], sys.argv[2])
    print_metrics(results)
