# Phase 1 Baseline Report — Data Pipeline & RAG Evaluation

> **Generated Date:** Automatically produced by Observability Module

---

## 1. Data Ingestion & Source Summary

| Attribute | Value |
|---|---|
| **Data Source** | Crossref REST API |
| **Search Query** | `agentic retrieval augmented generation large language model` |
| **Raw Records Fetched** | 24 |
| **Clean Records Output** | 24 |

---

## 2. RAG Baseline Evaluation Metrics

| Metric Name | Value | Description |
|---|---|---|
| **Retrieval Hit Rate** | `1.0000` | Tỉ lệ tìm thấy đúng document context |
| **Mean Token F1** | `0.9000` | Độ chính xác token của câu trả lời |
| **LLM Judge Accuracy** | `0.8667` | Tỉ lệ LLM Judge đánh giá đúng/đạt |
| **Mean LLM Judge Score** | `4.4667` | Điểm số trung bình từ LLM Judge |

---

## 3. Data Quality Observability

- **Overall Status:** PASS
- **Detected Failures:** `None`

### Quality Detailed Breakdown

| Check Item | Value | Status |
|---|---|---|
| **Total Row Count** | 24 | — |
| **Null Paper IDs** | 0 | ✅ Pass |
| **Duplicate Paper IDs** | 0 | ✅ Pass |
| **Null Titles** | 0 | ✅ Pass |
| **Short / Blank Summaries** | 0 | ✅ Pass |

---

## 4. Data Freshness Observability

- **Freshness Status:** FRESH

| Metric | Value |
|---|---|
| **Latest Publication Date** | `2026-08-05` |
| **Oldest Publication Date** | `2026-02-12` |
| **Stale Rows Count** | `0` |
| **Total Rows Evaluated** | `24` |

---
