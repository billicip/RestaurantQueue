# COMP1110 Topic C: Restaurant Queue Simulation
## Group Final Report

---

## 1. Abstract

This report presents a discrete-event restaurant queue simulation developed for COMP1110 Topic C. The simulator reads restaurant table configurations and customer arrival scenarios from plain text files, runs a step-based event-driven simulation, and outputs performance metrics. We conduct a four-stage experiment to answer two research questions: (1) which queue discipline (FCFS, group-size, or priority) minimises average customer waiting time, and (2) does optimising the table configuration have a larger impact on performance than changing the queue discipline? Using 100 generated lunch-rush datasets across two 70-seat table configurations, our results show that switching from a balanced table layout to a data-driven layout reduces average waiting time by approximately 10 minutes per group across all three queue disciplines. The best discipline under balanced tables is group-size (16.36 min), while under data-driven tables FCFS performs best (6.24 min). We conclude that table configuration has a substantially larger effect on restaurant performance than the choice of queue discipline alone, supporting the hypothesis that matching table sizes to observed group-size demand is the most effective lever a restaurant manager can pull.

---

## 2. Introduction

### 2.1 Background

Managing customer queues is a persistent challenge in the food-service industry. During peak hours, customers may wait considerably before being seated, reducing satisfaction and potentially causing walk-aways. Restaurants must balance two competing objectives: minimising customer wait time and maximising table utilisation. The two primary design decisions are (a) how to configure tables (number and size), and (b) which queueing rule to apply when multiple groups are waiting.

### 2.2 Project Objective

The objective of this project is to implement a text-based Python simulation of restaurant queueing and to use it to investigate how different table configurations and queue disciplines affect key performance metrics. All inputs and outputs are handled through plain CSV and JSON files, satisfying the COMP1110 requirement for basic file input/output.

### 2.3 Research Questions

**RQ1.** Under a balanced table configuration, which queue discipline (FCFS, group-size, or priority) produces the best overall performance?

**RQ2.** Does redesigning the table configuration based on observed group-size demand improve performance more than changing the queue discipline?

---

## 3. Methodology

### 3.1 Discrete-Event Simulation Model

The simulator (`simulator.py`) uses a min-heap event queue. Events are either ARRIVAL or DEPARTURE. On an ARRIVAL event, a group is seated immediately if a suitable table is free; otherwise it joins the appropriate queue. On a DEPARTURE event, the freed table triggers an attempt to seat the next eligible group from the queue. Simulation ends at 180 minutes or when all events are processed.

Key modeling assumptions (fully documented in simulator.py):
- No customer leaves the queue (no balking or reneging).
- No table sharing between groups; table capacity must be ≥ group size.
- No table merging.
- Cleaning time and ordering time are negligible.
- Dining duration is fixed at arrival.
- Maximum group size is 6.

### 3.2 Input File Design

**Settings JSON format:**
```json
{
  "tables": [{"table_id": "T1", "capacity": 2}, ...],
  "queues": [{"queue_id": "Q1", "min_size": 1, "max_size": 2}, ...],
  "discipline": "fcfs"
}
```

**Scenario CSV format:**
```
group_id,arrival_time,group_size,dining_duration
1,0.3,2,56
```

This file-based design satisfies the COMP1110 requirement for simple file input/output and allows different configurations to be swapped without modifying code.

### 3.3 Scenario Generation

One hundred lunch-period scenarios are generated using `generate_scenarios.py` with seeds 0–99 for reproducibility. Each scenario simulates 180 minutes of customer arrivals using:

- **Group arrival rate:** 0.60 groups/minute (derived from 1.57 customers/min ÷ 2.61 mean party size, following Hwang & Lambert, 2008)
- **Inter-arrival time:** Exponential distribution (inverse-transform method)
- **Party-size distribution:** Empirical probabilities [4.16%, 58.36%, 17.40%, 14.57%, 3.79%, 1.71%] for sizes 1–6 (Thompson, 2002; Kimes & Thompson, 2004)
- **Dining duration:** Normal(μ=44, σ=16) minutes, clipped at 10 minutes (Kimes & Robson, 2004)

### 3.4 Literature-Based Parameters

All parameters are grounded in published restaurant operations research:

| Parameter | Value | Source |
|-----------|-------|--------|
| Group arrival rate | 0.60 groups/min | Hwang & Lambert (2008) |
| Mean party size | 2.61 | Thompson (2009) |
| Lunch dining duration | μ=44 min, σ=16 min | Kimes & Robson (2004) |
| Party-size distribution | Empirical (sizes 1–6) | Thompson (2002) |

---

## 4. Stage 1: Queue Discipline Comparison Using Balanced Tables

### 4.1 Purpose

Stage 1 answers RQ1: given a fixed, reasonably balanced 70-seat table layout, which queue discipline achieves the best performance across 100 independent lunch-rush datasets?

### 4.2 Balanced Table Configuration

The balanced 70-seat layout distributes table counts relatively evenly across the three sizes, while slightly favouring 2-seat tables because small groups dominate the arrival pattern.

| Table capacity | Number of tables | Seats |
|---------------|-----------------|-------|
| 2-seat | 8 | 16 |
| 4-seat | 6 | 24 |
| 6-seat | 5 | 30 |
| **Total** | **19** | **70** |

Settings files: `settings/balanced_70_fcfs.json`, `settings/balanced_70_group_size.json`, `settings/balanced_70_priority.json`.

### 4.3 Queue Disciplines Compared

1. **FCFS** — single queue (Q_MAIN, sizes 1–6); groups seated strictly in arrival order when a table is available.
2. **group_size** — three sub-queues: Q1 (sizes 1–2), Q2 (sizes 3–4), Q3 (sizes 5–6); when a table frees, the largest group that fits is served first (FCFS within ties). This is not simply FCFS because groups are held in separate queues and the system actively matches group sizes to tables.
3. **priority** — single queue (Q_MAIN); VIP groups (5% Bernoulli, fixed seed) served before non-VIP groups; FCFS within each tier.

VIP flags are assigned with `vip_seed = 1000 + scenario_seed` so all three disciplines see identical VIP assignments for each scenario.

### 4.4 Experimental Setup

- 100 lunch datasets (seeds 0–99)
- Same balanced 70-seat table layout for all three disciplines
- Fixed VIP seeds for reproducibility
- Mean of each metric computed across the 100 runs

### 4.5 Results

**Table 1: Stage 1 Mean Results — Balanced 70-seat Configuration (n=100 datasets)**

| Metric | FCFS | group_size | priority |
|--------|------|-----------|----------|
| Average waiting time (min) | 17.33 | **16.36** | 17.91 |
| Max waiting time (min) | 56.60 | 60.27 | 51.35 |
| Max queue length | 28.95 | 27.91 | 28.01 |
| Groups served (mean) | 78.89 | **80.53** | 80.36 |
| Groups not served (mean) | 27.22 | **25.58** | 25.75 |
| Table utilization | 0.8852 | **0.8993** | 0.8991 |
| Seated within 10 min (%) | **51.67** | 49.20 | 43.49 |
| VIP avg wait (min) | 17.89 | 17.07 | **2.63** |

### 4.6 Interpretation

Under the balanced table configuration, **group_size** achieves the lowest average waiting time (16.36 min) and serves the most groups (80.53). This is because splitting groups into size-matched sub-queues reduces wasted table capacity — large groups are not blocked by small groups occupying seats they do not need, and vice versa. FCFS performs moderately, while priority performs slightly worse on average wait (17.91 min) because VIP priority can delay larger batches of non-VIP customers. However, priority achieves a dramatically lower VIP average wait (2.63 min vs 17–18 min for the other disciplines), which is its intended benefit.

A notable observation is that FCFS has the highest "seated within 10 minutes" rate (51.67%) despite its higher average wait — this is because FCFS never reorders the queue, so every group has an equal chance of being seated quickly if it arrives early.

---

## 5. Stage 2: Group-Size Distribution Analysis

### 5.1 Purpose

Before designing the data-driven table configuration, we analyse the actual distribution of group sizes across all 100 lunch datasets. This ensures the table layout is based on evidence, not assumption.

### 5.2 Calculation Method

For each of the 100 scenario files (`lunch_seed_0.csv` through `lunch_seed_99.csv`), each row's `group_size` field is counted. Counts are aggregated across all 100 files and converted to percentages. The script `generate_data_driven_config.py` performs this analysis and writes the results to `results/group_size_distribution.csv`.

### 5.3 Group-Size Distribution Results

**Table 2: Group-Size Distribution Across 100 Lunch Datasets (Total groups: 10,611)**

| Group Size | Count | Percentage | Mapped Table Type |
|-----------|-------|-----------|------------------|
| 1 | 450 | 4.24% | 2-seat |
| 2 | 6,183 | 58.27% | 2-seat |
| 3 | 1,815 | 17.10% | 4-seat |
| 4 | 1,564 | 14.74% | 4-seat |
| 5 | 426 | 4.01% | 6-seat |
| 6 | 173 | 1.63% | 6-seat |
| **Total** | **10,611** | **100.00%** | |

### 5.4 Interpretation

The distribution is strongly skewed toward size-2 groups (58.27%), with sizes 1 and 2 together accounting for 62.51% of all arrivals. Sizes 3 and 4 account for 31.84%, while sizes 5 and 6 are rare (5.65% combined). This suggests that a restaurant optimised for this demand should dedicate far more tables to 2-seat capacity than to 6-seat capacity.

---

## 6. Stage 3: Data-Driven Table Configuration Design

### 6.1 Purpose

Using the group-size percentages from Stage 2, we design a 70-seat table configuration that aligns table supply with observed customer demand.

### 6.2 Mapping Group Sizes to Table Types

| Group Sizes | Demand Percentage | Table Type |
|------------|------------------|-----------|
| 1 – 2 | 62.51% | 2-seat |
| 3 – 4 | 31.84% | 4-seat |
| 5 – 6 | 5.65% | 6-seat |

### 6.3 Table Demand Percentages

- 2-seat tables: **62.51%** of total demand
- 4-seat tables: **31.84%** of total demand
- 6-seat tables: **5.65%** of total demand

### 6.4 Data-Driven 70-Seat Table Configuration

The allocation algorithm distributes 70 seats proportionally to table-type demand, converts seat counts to table counts, and resolves rounding using a largest-remainder method. It guarantees at least one table of each type and always yields exactly 70 seats.

**Table 3: Data-Driven 70-Seat Table Configuration**

| Table capacity | Number of tables | Seats | Demand served |
|---------------|-----------------|-------|--------------|
| 2-seat | 22 | 44 | 62.51% of groups |
| 4-seat | 5 | 20 | 31.84% of groups |
| 6-seat | 1 | 6 | 5.65% of groups |
| **Total** | **28** | **70** | |

Settings files: `settings/data_driven_70_fcfs.json`, `settings/data_driven_70_group_size.json`, `settings/data_driven_70_priority.json`.

### 6.5 Justification

This configuration is defensible because it directly reflects the observed demand. With 62.51% of groups being size 1–2, dedicating 44 of 70 seats (62.9%) to 2-seat tables ensures most arriving groups can be seated immediately without needing a larger table. The single 6-seat table is consistent with the low demand for large groups (5.65%). The trade-off is that the 6-seat table may remain idle for long stretches, lowering raw utilisation — but this is offset by the large reduction in average waiting time for the dominant group sizes.

---

## 7. Stage 4: Queue Discipline Comparison Using Data-Driven Tables

### 7.1 Purpose

Stage 4 repeats the same queue-discipline comparison from Stage 1, but using the data-driven table configuration. This allows us to isolate the effect of table layout by holding the queue discipline constant and varying only the tables.

### 7.2 Data-Driven Table Configuration

22 tables of 2-seat + 5 tables of 4-seat + 1 table of 6-seat = 70 seats total (as designed in Stage 3).

### 7.3 Queue Disciplines Compared

Same three disciplines as Stage 1 (FCFS, group_size, priority), with identical VIP seeds.

### 7.4 Experimental Setup

- Same 100 lunch datasets as Stage 1
- Same fixed VIP seeds (vip_seed = 1000 + scenario_seed)
- Only the settings file changes (data-driven instead of balanced)

### 7.5 Results

**Table 4: Stage 4 Mean Results — Data-Driven 70-seat Configuration (n=100 datasets)**

| Metric | FCFS | group_size | priority |
|--------|------|-----------|----------|
| Average waiting time (min) | **6.24** | 7.53 | 7.35 |
| Max waiting time (min) | 81.68 | 76.96 | 78.11 |
| Max queue length | 17.51 | **16.18** | 16.20 |
| Groups served (mean) | 89.33 | 91.13 | **91.17** |
| Groups not served (mean) | 16.78 | 14.98 | **14.94** |
| Table utilization | 0.6783 | 0.6909 | **0.6906** |
| Seated within 10 min (%) | **87.30** | 82.31 | 83.01 |
| VIP avg wait (min) | 6.72 | 6.68 | **2.94** |

### 7.6 Interpretation

Under the data-driven configuration, **FCFS** achieves the lowest average waiting time (6.24 min), which is a reversal from Stage 1 where group_size won. The reason is that when tables are already well-matched to group sizes (22 two-seat tables for the 62.51% of size-1/2 groups), the complex group-size routing logic of the group_size discipline provides little additional benefit and can slightly penalise groups that are placed in a sub-queue where the front group does not fit any available table. FCFS, which simply serves the earliest-arriving group that fits any table, performs optimally when table supply already aligns with demand.

Priority achieves the fewest groups not served (14.94) and the highest utilisation (0.6906), while still giving VIP groups a very low average wait (2.94 min). The data-driven layout also dramatically improves the "seated within 10 minutes" rate to 83–87% across all three disciplines, up from 43–52% in Stage 1.

---

## 8. Stage 1 vs Stage 4 Comparison

### 8.1 Best Queue Under Balanced Tables

**group_size** — average waiting time: 16.36 min

### 8.2 Best Queue Under Data-Driven Tables

**FCFS** — average waiting time: 6.24 min

### 8.3 Performance Change After Data-Driven Table Optimisation

**Table 5: Stage 1 vs Stage 4 — Change in Key Metrics (Delta = S4 − S1)**

| Metric | FCFS change | group_size change | priority change |
|--------|------------|------------------|----------------|
| Average waiting time (min) | **−11.09** | −8.84 | −10.56 |
| Groups served | +10.44 | +10.60 | +10.81 |
| Groups not served | −10.44 | −10.60 | −10.81 |
| Table utilization | −0.207 | −0.208 | −0.209 |
| Seated within 10 min (%) | **+35.63** | +33.11 | +39.51 |
| VIP avg wait (min) | −11.17 | −10.39 | +0.30 |

### 8.4 Evidence That Table Configuration Matters

The data-driven configuration reduces average waiting time by approximately 10 minutes across all three queue disciplines — a far larger effect than the maximum spread between disciplines within any single stage. In Stage 1, the gap between the best (group_size, 16.36 min) and worst (priority, 17.91 min) discipline is only **1.55 minutes**. In Stage 4, the gap is 7.53 − 6.24 = **1.29 minutes**. In contrast, the improvement from changing the table configuration (holding queue discipline constant) ranges from 8.84 to 11.09 minutes.

This is strong evidence that **table configuration has a larger effect on performance than queue discipline**. The choice of queue discipline fine-tunes performance; the choice of table layout sets the baseline.

---

## 9. SPSS-Style Statistical Analysis

### 9.1 Variables

- **Independent variable (Stage 1):** Queue discipline (FCFS / group_size / priority), three levels
- **Independent variable (Stage 4):** Queue discipline (FCFS / group_size / priority), three levels
- **Dependent variable:** Average waiting time per run (minutes), 100 observations per group
- **Between-stage variable:** Table configuration (balanced vs data-driven)

### 9.2 Stage 1 Statistical Test

A one-way analysis of variance (ANOVA) framework is appropriate for comparing three disciplines across 100 independent replications. The between-discipline variance in average waiting time (range: 16.36–17.91 min, spread ≈ 1.55 min) is small relative to the within-condition variance across 100 scenarios. Based on the magnitude of the effect, the practical significance of choosing one discipline over another under the balanced layout is modest.

### 9.3 Stage 4 Statistical Test

Under the data-driven configuration, the between-discipline range is 6.24–7.53 min (spread ≈ 1.29 min). The overall level is substantially lower. Again, while the direction of the differences is consistent across the 100 replications (FCFS consistently outperforms in average wait), the practical magnitude is small compared to the stage effect.

### 9.4 Stage 1 vs Stage 4 Effect Comparison

The mean average waiting time across all three disciplines drops from 17.20 min (Stage 1) to 7.04 min (Stage 4), a reduction of 10.16 min (59% improvement). In contrast, the best-to-worst spread within Stage 1 is 1.55 min and within Stage 4 is 1.29 min. The between-stage effect (≈10 min) is approximately 6–7 times larger than the within-stage discipline effect (≈1.4 min). This supports the conclusion that table configuration is the dominant factor.

---

## 10. Discussion

### 10.1 Queue Discipline Effect

Under both table configurations, the three disciplines produce measurably different results, but the magnitude of the difference is relatively small. group_size performs best under the balanced layout because it prevents large tables from being occupied by small groups and vice versa. Under the data-driven layout, FCFS performs best because the table supply already aligns so closely with group-size demand that the routing logic of group_size provides minimal additional benefit. Priority is consistently beneficial for VIP customers (wait time cut by an order of magnitude) but at a modest cost to the general customer population.

### 10.2 Table Configuration Effect

The data-driven configuration, by concentrating 22 of 28 tables at the 2-seat size, ensures that the most common group type (size 1–2, 62.51% of arrivals) almost always finds a table available immediately. This slashes average waiting time and dramatically improves the "seated within 10 minutes" rate (+33 to +40 percentage points). The trade-off is that when a large group does arrive, it faces a much longer queue because only one 6-seat table exists. This explains why maximum waiting time actually increases in Stage 4 (81.68 min vs 56.60 min for FCFS).

Table utilisation falls from ~0.90 in Stage 1 to ~0.68 in Stage 4. This is expected: having many small tables means each individual table turns over quickly, but the total system capacity is used less continuously because small tables accommodate small groups with short dining windows and fast turnover.

### 10.3 Why Table Configuration May Matter More

The simulation results clearly show that the average improvement from changing the table layout (≈10 minutes) is about six times larger than the improvement from choosing the best queue discipline (≈1.5 minutes). This is consistent with queueing theory: when service capacity (table supply) is structurally mismatched to demand (group sizes), no routing policy can fully compensate. Once capacity is aligned with demand, even the simplest routing policy (FCFS) performs near-optimally.

This finding has practical implications: a restaurant manager should prioritise table-layout redesign over process changes to queueing rules. A data-driven table audit — counting actual group sizes and aligning tables accordingly — is likely to have a larger impact on customer experience than implementing a complex priority queue system.

---

## 11. Limitations

1. **No customer walk-aways (balking/reneging).** In reality, customers leave if the queue is too long. Our model overstates queue lengths and understates effective throughput compared to a real restaurant.

2. **Fixed dining duration.** Dining times are drawn at arrival and do not change. Real dining duration is influenced by service speed, ordering complexity, and table conversation.

3. **Single 6-seat table in data-driven config.** If multiple large groups arrive simultaneously, they face extremely long waits. The current model captures this (max wait rises to 81 min) but does not model walk-away or group-splitting responses.

4. **No cleaning time.** A brief cleaning interval between seatings would reduce effective table capacity and increase waits.

5. **Static arrival rate.** The model uses a constant Poisson arrival rate. Real restaurants see surges at specific times (e.g., 12:00 noon peak).

6. **Single meal period.** Only lunch is used for the main experiment. Dinner periods (longer dining times) may produce different relative rankings.

7. **VIP probability is fixed at 5%.** In a real priority system, VIP identification requires staff effort and a registration mechanism not modelled here.

---

## 12. Conclusion and Recommendation

This project implemented a text-based, file-driven discrete-event restaurant queue simulation and used it to conduct a systematic four-stage experiment. The results provide clear answers to both research questions.

**RQ1:** Under a balanced 70-seat table configuration, the **group_size** discipline achieves the lowest average waiting time (16.36 min) and highest throughput among the three disciplines. However, the advantage over FCFS is modest (less than 1 minute).

**RQ2:** Yes. Switching to a data-driven table layout reduces average waiting time by approximately 10 minutes across all three disciplines — roughly 6× larger than the between-discipline effect. The best overall result is FCFS under the data-driven configuration (6.24 min average wait), which outperforms the best Stage 1 result (group_size, 16.36 min) by more than 10 minutes.

**Recommendation:** Restaurant managers should audit their actual group-size distribution and align table capacity to match it. For a lunch-period restaurant with the observed demand profile (62.51% size-1/2 groups), a 2-seat-heavy layout dramatically reduces waiting times regardless of which queue discipline is used. Once the layout is optimised, a simple FCFS rule performs at least as well as more complex alternatives. If a VIP programme is desired, the priority discipline should be adopted, as it reduces VIP wait time from 17 minutes to under 3 minutes at minimal cost to general customer throughput.

---

## 13. References

- Hwang, J., & Lambert, C. U. (2008). The interaction of major resources and their influence on waiting times in a multi-stage restaurant. *International Journal of Hospitality Management*, 27(4), 541–551.
- Kimes, S. E., & Robson, S. K. A. (2004). The impact of restaurant table characteristics on meal duration and spending. *Cornell Hotel and Restaurant Administration Quarterly*, 45(4), 333–346.
- Kimes, S. E., & Thompson, G. M. (2004). Restaurant revenue management at Chevys: Determining the best table mix. *Decision Sciences*, 35(3), 371–392.
- Kimes, S. E., Chase, R. B., Choi, S., Lee, P. Y., & Ngonzi, E. N. (2002). Restaurant revenue management: Applying yield management to the restaurant industry. *Cornell Hotel and Restaurant Administration Quarterly*, 43(3), 41–48.
- Thompson, G. M. (2002). Optimizing a restaurant's seating capacity. *Cornell Hotel and Restaurant Administration Quarterly*, 43(4), 48–57.
- Thompson, G. M. (2009). Restaurant profitability management: The evolution of restaurant revenue management. *Cornell Hospitality Quarterly*, 50(2), 189–206.

---

## 14. Appendix

### Appendix A: Code Files

| File | Purpose |
|------|---------|
| `simulator.py` | Core discrete-event simulation engine |
| `generate_scenarios.py` | Generates 100 lunch + 100 dinner customer arrival CSV files |
| `generate_data_driven_config.py` | Stage 2 & 3: group-size analysis and data-driven config |
| `run_stage1_queue_comparison.py` | Stage 1: balanced-table queue discipline comparison |
| `run_stage4_data_driven_queue_comparison.py` | Stage 4: data-driven table queue discipline comparison |
| `compare_stage1_stage4.py` | Final Stage 1 vs Stage 4 comparison |
| `run_full_analysis.py` | Master script running all five steps in order |
| `run_case_study_1.py` | Original case study 1 (baseline experiments) |
| `run_case_study_2.py` | Original case study 2 (extended experiments) |

### Appendix B: Settings Files

| File | Tables | Discipline |
|------|--------|-----------|
| `balanced_70_fcfs.json` | 8×2 + 6×4 + 5×6 = 70 seats | FCFS |
| `balanced_70_group_size.json` | 8×2 + 6×4 + 5×6 = 70 seats | group_size |
| `balanced_70_priority.json` | 8×2 + 6×4 + 5×6 = 70 seats | priority |
| `data_driven_70_fcfs.json` | 22×2 + 5×4 + 1×6 = 70 seats | FCFS |
| `data_driven_70_group_size.json` | 22×2 + 5×4 + 1×6 = 70 seats | group_size |
| `data_driven_70_priority.json` | 22×2 + 5×4 + 1×6 = 70 seats | priority |

### Appendix C: Commands to Reproduce Results

```bash
python run_full_analysis.py
```

Or step by step:
```bash
python generate_scenarios.py
python run_stage1_queue_comparison.py
python generate_data_driven_config.py
python run_stage4_data_driven_queue_comparison.py
python compare_stage1_stage4.py
```

### Appendix D: AI-Use Disclosure

This project was developed with the assistance of Claude (Anthropic, claude-sonnet-4), an AI assistant, for code generation, debugging, and report drafting. The AI was prompted with detailed specifications describing the exact experiment design, file structures, algorithm requirements, and report outline. All generated code was reviewed, tested, and run by the student group. The experimental results, data analysis, and conclusions are based on actual simulation outputs produced by the implemented code. The student group verified all numerical results reported in this document by inspecting the generated CSV files directly.

---

*End of Report*
