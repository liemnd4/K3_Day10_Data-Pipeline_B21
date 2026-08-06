# Data Corruption & Repair Observability Comparison Report

> **Objective:** Evaluate the impact of intentional data corruption on RAG agent accuracy and demonstrate data recovery via automated repair.

---

## 1. Executive Metrics Comparison (Baseline vs Corrupted vs Repaired)

| Metric Name | Baseline (Clean) | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Corrupted) |
|---|---|---|---|---|---|
| **Retrieval Hit Rate** | `1.0000` | `0.8000` | `1.0000` | `-0.2000` | `+0.2000` |
| **Mean Token F1** | `0.9000` | `0.6565` | `0.9000` | `-0.2435` | `+0.2435` |
| **LLM Judge Accuracy** | `0.8667` | `0.6167` | `0.8667` | `-0.2500` | `+0.2500` |
| **Mean LLM Judge Score** | `4.4667` | `3.6000` | `4.4833` | `-0.8667` | `+0.8833` |

---

## 2. Data Quality Comparison

| Quality Check Attribute | Corrupted State | Repaired State |
|---|---|---|
| **Overall Quality Status** | ❌ FAIL | PASS |
| **Detected Failures** | `paper_id_duplicate_check, summary_short_check` | `None` |
| **Total Row Count** | 23 | 24 |
| **Null Paper IDs** | 0 | 0 |
| **Duplicate Paper IDs** | 2 | 0 |
| **Null Titles** | 0 | 0 |
| **Short / Blank Summaries** | 2 | 0 |

---

## 3. Data Freshness Comparison

| Freshness Metric | Corrupted State | Repaired State |
|---|---|---|
| **Freshness Status** | 🔴 STALE | FRESH |
| **Latest Published Date** | `2026-07-03` | `2026-08-05` |
| **Oldest Published Date** | `1990-01-01` | `2026-02-12` |
| **Stale Rows Count** | `2` | `0` |
| **Total Evaluated Rows** | `23` | `24` |

---

## 4. Key Takeaways & Observability Conclusions

1. **Impact of Data Corruption:**
   - Injecting data flaws (blank/noisy summaries, stale dates, duplicate records) directly degrades retrieval accuracy and LLM answer scores.
   - Observability checks successfully flag data anomalies (`checks_passed = False`) before incorrect answers reach the user.

2. **Effectiveness of Data Repair:**
   - Re-ingesting and re-cleaning data from the raw source (`data/raw/`) restores quality checks (`checks_passed = True`) and brings RAG metrics back to Baseline standards.
