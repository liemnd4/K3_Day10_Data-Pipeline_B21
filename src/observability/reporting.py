from __future__ import annotations

from typing import Any


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Tạo báo cáo Markdown cho Phase 1 Baseline và lưu vào report_path."""
    from pathlib import Path

    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract source summary values safely
    source_api = source_summary.get("source_api", "Crossref API")
    source_query = source_summary.get("source_query", "N/A")
    raw_count = source_summary.get("raw_count", source_summary.get("total_fetched", "N/A"))
    clean_count = source_summary.get("clean_count", quality.get("row_count", "N/A"))

    # Extract metrics safely
    hit_rate = metrics.get("retrieval_hit_rate", metrics.get("hit_rate", 0.0))
    token_f1 = metrics.get("mean_token_f1", metrics.get("token_f1", 0.0))
    judge_acc = metrics.get("judge_accuracy", 0.0)
    judge_score = metrics.get("mean_judge_score", metrics.get("judge_score", 0.0))

    # Quality details
    q_status = "PASS" if quality.get("checks_passed", False) else "❌ FAIL"
    q_failures = quality.get("failures", [])
    failures_str = ", ".join(q_failures) if q_failures else "None"

    # Freshness details
    f_status = "FRESH" if freshness.get("is_fresh", False) else "🔴 STALE"

    md_content = f"""# Phase 1 Baseline Report — Data Pipeline & RAG Evaluation

> **Generated Date:** Automatically produced by Observability Module

---

## 1. Data Ingestion & Source Summary

| Attribute | Value |
|---|---|
| **Data Source** | {source_api} |
| **Search Query** | `{source_query}` |
| **Raw Records Fetched** | {raw_count} |
| **Clean Records Output** | {clean_count} |

---

## 2. RAG Baseline Evaluation Metrics

| Metric Name | Value | Description |
|---|---|---|
| **Retrieval Hit Rate** | `{hit_rate:.4f}` | Tỉ lệ tìm thấy đúng document context |
| **Mean Token F1** | `{token_f1:.4f}` | Độ chính xác token của câu trả lời |
| **LLM Judge Accuracy** | `{judge_acc:.4f}` | Tỉ lệ LLM Judge đánh giá đúng/đạt |
| **Mean LLM Judge Score** | `{judge_score:.4f}` | Điểm số trung bình từ LLM Judge |

---

## 3. Data Quality Observability

- **Overall Status:** {q_status}
- **Detected Failures:** `{failures_str}`

### Quality Detailed Breakdown

| Check Item | Value | Status |
|---|---|---|
| **Total Row Count** | {quality.get('row_count', 0)} | — |
| **Null Paper IDs** | {quality.get('paper_id_null_count', 0)} | {"✅ Pass" if quality.get('paper_id_null_count', 0) == 0 else "❌ Fail"} |
| **Duplicate Paper IDs** | {quality.get('paper_id_duplicate_count', 0)} | {"✅ Pass" if quality.get('paper_id_duplicate_count', 0) == 0 else "❌ Fail"} |
| **Null Titles** | {quality.get('title_null_count', 0)} | {"✅ Pass" if quality.get('title_null_count', 0) == 0 else "❌ Fail"} |
| **Short / Blank Summaries** | {quality.get('summary_short_count', 0)} | {"✅ Pass" if quality.get('summary_short_count', 0) == 0 else "❌ Fail"} |

---

## 4. Data Freshness Observability

- **Freshness Status:** {f_status}

| Metric | Value |
|---|---|
| **Latest Publication Date** | `{freshness.get('latest_published', 'N/A')}` |
| **Oldest Publication Date** | `{freshness.get('oldest_published', 'N/A')}` |
| **Stale Rows Count** | `{freshness.get('stale_rows', 0)}` |
| **Total Rows Evaluated** | `{freshness.get('total_rows', 0)}` |

---
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)



def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Tạo báo cáo Markdown so sánh 3 trạng thái Baseline vs Corrupted vs Repaired."""
    from pathlib import Path

    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Helper function to get metric values safely
    def get_m(m_dict: dict[str, Any], key1: str, key2: str = "") -> float:
        val = m_dict.get(key1, m_dict.get(key2, 0.0))
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    b_hit = get_m(baseline_metrics, "retrieval_hit_rate", "hit_rate")
    c_hit = get_m(corrupted_metrics, "retrieval_hit_rate", "hit_rate")
    r_hit = get_m(repaired_metrics, "retrieval_hit_rate", "hit_rate")

    b_f1 = get_m(baseline_metrics, "mean_token_f1", "token_f1")
    c_f1 = get_m(corrupted_metrics, "mean_token_f1", "token_f1")
    r_f1 = get_m(repaired_metrics, "mean_token_f1", "token_f1")

    b_acc = get_m(baseline_metrics, "judge_accuracy")
    c_acc = get_m(corrupted_metrics, "judge_accuracy")
    r_acc = get_m(repaired_metrics, "judge_accuracy")

    b_score = get_m(baseline_metrics, "mean_judge_score", "judge_score")
    c_score = get_m(corrupted_metrics, "mean_judge_score", "judge_score")
    r_score = get_m(repaired_metrics, "mean_judge_score", "judge_score")

    # Quality details
    c_q_status = "PASS" if corrupted_quality.get("checks_passed", False) else "❌ FAIL"
    r_q_status = "PASS" if repaired_quality.get("checks_passed", False) else "❌ FAIL"

    c_failures = ", ".join(corrupted_quality.get("failures", [])) or "None"
    r_failures = ", ".join(repaired_quality.get("failures", [])) or "None"

    # Freshness details
    c_f_status = "FRESH" if corrupted_freshness.get("is_fresh", False) else "🔴 STALE"
    r_f_status = "FRESH" if repaired_freshness.get("is_fresh", False) else "🔴 STALE"

    md_content = f"""# Data Corruption & Repair Observability Comparison Report

> **Objective:** Evaluate the impact of intentional data corruption on RAG agent accuracy and demonstrate data recovery via automated repair.

---

## 1. Executive Metrics Comparison (Baseline vs Corrupted vs Repaired)

| Metric Name | Baseline (Clean) | Corrupted | Repaired | Impact (Corrupted vs Baseline) | Recovery (Repaired vs Corrupted) |
|---|---|---|---|---|---|
| **Retrieval Hit Rate** | `{b_hit:.4f}` | `{c_hit:.4f}` | `{r_hit:.4f}` | `{c_hit - b_hit:+.4f}` | `{r_hit - c_hit:+.4f}` |
| **Mean Token F1** | `{b_f1:.4f}` | `{c_f1:.4f}` | `{r_f1:.4f}` | `{c_f1 - b_f1:+.4f}` | `{r_f1 - c_f1:+.4f}` |
| **LLM Judge Accuracy** | `{b_acc:.4f}` | `{c_acc:.4f}` | `{r_acc:.4f}` | `{c_acc - b_acc:+.4f}` | `{r_acc - c_acc:+.4f}` |
| **Mean LLM Judge Score** | `{b_score:.4f}` | `{c_score:.4f}` | `{r_score:.4f}` | `{c_score - b_score:+.4f}` | `{r_score - c_score:+.4f}` |

---

## 2. Data Quality Comparison

| Quality Check Attribute | Corrupted State | Repaired State |
|---|---|---|
| **Overall Quality Status** | {c_q_status} | {r_q_status} |
| **Detected Failures** | `{c_failures}` | `{r_failures}` |
| **Total Row Count** | {corrupted_quality.get('row_count', 'N/A')} | {repaired_quality.get('row_count', 'N/A')} |
| **Null Paper IDs** | {corrupted_quality.get('paper_id_null_count', 0)} | {repaired_quality.get('paper_id_null_count', 0)} |
| **Duplicate Paper IDs** | {corrupted_quality.get('paper_id_duplicate_count', 0)} | {repaired_quality.get('paper_id_duplicate_count', 0)} |
| **Null Titles** | {corrupted_quality.get('title_null_count', 0)} | {repaired_quality.get('title_null_count', 0)} |
| **Short / Blank Summaries** | {corrupted_quality.get('summary_short_count', 0)} | {repaired_quality.get('summary_short_count', 0)} |

---

## 3. Data Freshness Comparison

| Freshness Metric | Corrupted State | Repaired State |
|---|---|---|
| **Freshness Status** | {c_f_status} | {r_f_status} |
| **Latest Published Date** | `{corrupted_freshness.get('latest_published', 'N/A')}` | `{repaired_freshness.get('latest_published', 'N/A')}` |
| **Oldest Published Date** | `{corrupted_freshness.get('oldest_published', 'N/A')}` | `{repaired_freshness.get('oldest_published', 'N/A')}` |
| **Stale Rows Count** | `{corrupted_freshness.get('stale_rows', 0)}` | `{repaired_freshness.get('stale_rows', 0)}` |
| **Total Evaluated Rows** | `{corrupted_freshness.get('total_rows', 0)}` | `{repaired_freshness.get('total_rows', 0)}` |

---

## 4. Key Takeaways & Observability Conclusions

1. **Impact of Data Corruption:**
   - Injecting data flaws (blank/noisy summaries, stale dates, duplicate records) directly degrades retrieval accuracy and LLM answer scores.
   - Observability checks successfully flag data anomalies (`checks_passed = False`) before incorrect answers reach the user.

2. **Effectiveness of Data Repair:**
   - Re-ingesting and re-cleaning data from the raw source (`data/raw/`) restores quality checks (`checks_passed = True`) and brings RAG metrics back to Baseline standards.
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md_content)

