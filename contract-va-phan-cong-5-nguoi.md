# Day 10 — Data Pipeline & Data Observability: Contract & Phân công 5 người

Repo: `K3_Day10_Data-Pipeline-Data-Observability`
Mục tiêu: hoàn thành `TODO(student)` trong `src/`, chạy được `run_phase1.py` và `run_corruption_flow.py` end-to-end.

---

## 1. Nguyên tắc chung

- **Contract chốt trước, code sau.** 5 người có thể code song song vì mỗi module chỉ cần đúng field/type đã thống nhất ở đây, không cần đợi người khác code xong mới bắt đầu.
- Mọi thay đổi field trong contract phải báo cho người dùng field đó (đặc biệt: Cleaning đổi field → Evaluation, Observability, Integration đều bị ảnh hưởng).
- Không hard-code path — luôn lấy từ `Settings.paths` (`src/core/config.py`), đã định nghĩa sẵn toàn bộ đường dẫn output.
- Không được làm mất record âm thầm: mọi bước filter/dedupe/drop phải log lại count + lý do.

---

## 2. Bốn contract dữ liệu (đọc kỹ trước khi code)

### Contract A — Raw record (`PaperRecord`)

File sở hữu: `src/ingestion/crossref.py` (đã định nghĩa sẵn dataclass, chỉ cần implement logic parse).

```python
@dataclass(frozen=True)
class PaperRecord:
    paper_id: str          # BẮT BUỘC stable — dùng DOI (hoặc slug từ DOI), không random/index
    title: str
    summary: str            # abstract, có thể rỗng nếu Crossref không có, nhưng field phải tồn tại
    authors: list[str]
    categories: list[str]
    primary_category: str   # categories[0] nếu có, else ""
    published: str           # ISO date string "YYYY-MM-DD"
    updated: str              # ISO date string, fallback = published nếu Crossref không có
    abs_url: str
    pdf_url: str              # có thể rỗng nếu Crossref không cung cấp link PDF
    comment: str               # optional, có thể rỗng
```

**Ai tạo:** Ingestion
**Ai tiêu thụ:** Cleaning (input trực tiếp), Integration (gọi `fetch_source_records` / `load_raw_records` trong pipeline)

**Ràng buộc bắt buộc:**
- `paper_id` không trùng, không đổi giữa các lần fetch cùng 1 DOI (đây là khóa nối xuyên suốt raw → clean → index → eval).
- Record thiếu DOI hoặc thiếu title → loại bỏ, không đưa vào list trả về.
- Raw response gốc (JSON thô từ Crossref) phải được lưu **trước khi parse**, vào `settings.paths.raw_api_response`.
- Raw records đã parse lưu vào `settings.paths.raw_records_json`.

---

### Contract B — Clean DataFrame

File sở hữu: `src/ingestion/cleaning.py` → hàm `build_clean_dataframe(records, run_date) -> pd.DataFrame`.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `paper_id` | str | unique, không null — khóa chính |
| `title` | str | normalize whitespace |
| `summary` | str | normalize whitespace, có thể rỗng nhưng không NaN (dùng `""`) |
| `authors_joined` | str | `", ".join(authors)` |
| `categories_joined` | str | `", ".join(categories)` |
| `primary_category` | str | |
| `published` | str (ISO date) | parse được bằng `pd.to_datetime` |
| `updated` | str (ISO date) | |
| `age_days` | int | `(run_date - published).days`, dùng cho freshness |
| `summary_chars` | int | `len(summary)` |
| `text_for_embedding` | str | ghép title + summary (+ có thể categories) — đây là input embedding, KHÔNG được rỗng |
| `abs_url`, `pdf_url`, `comment` | str | giữ nguyên từ raw |

**Ai tạo:** Cleaning
**Ai tiêu thụ:** Evaluation (chọn paper để build câu hỏi), Observability (quality/freshness check), Integration (build embedding index), Corruption (input để corrupt)

**Ràng buộc bắt buộc:**
- Dedupe theo `paper_id` — giữ 1 bản ghi duy nhất/paper_id.
- Drop row không có `text_for_embedding` hợp lệ (rỗng hoặc quá ngắn).
- Log số row bị loại + lý do (raw count → clean count phải giải thích được).
- Output ghi cả CSV (`clean_csv`) và JSON (`clean_json`).

---

### Contract C — Evaluation test set item

File sở hữu: `src/evaluation/testset.py` → hàm `build_test_set(df, output_path) -> list[dict]`.

```python
{
    "id": str,                          # unique trong test set
    "question_type": str,               # "summary" | "authors" | "date" | "categories"
    "question": str,
    "ground_truth": str,
    "ground_truth_doc_ids": list[str],  # PHẢI là paper_id có thật trong clean dataframe
}
```

**Ai tạo:** Evaluation
**Ai tiêu thụ:** `metrics.py` (`evaluate_pipeline`, đã có sẵn code — chỉ đọc field theo đúng tên trên), Integration (gọi trong `phase1.py`)

**Ràng buộc bắt buộc:**
- Không tự bịa `ground_truth_doc_ids` — phải trace được từ `paper_id` thật trong clean data.
- Tối thiểu đủ 4 loại câu hỏi (summary/authors/date/categories), mỗi loại từ nhiều paper khác nhau.
- Kiểm tra số lượng document tối thiểu trước khi build (nếu ít quá thì cảnh báo/raise).

---

### Contract D — Quality & Freshness report

File sở hữu: `src/observability/quality.py`, `src/observability/reporting.py`.

`run_data_quality_checks(df, settings, report_name) -> dict`:
```python
{
    "report_name": str,
    "row_count": int,
    "paper_id_null_count": int,
    "paper_id_duplicate_count": int,
    "title_null_count": int,
    "summary_short_count": int,   # summary quá ngắn / rỗng
    "checks_passed": bool,
    "failures": list[str],         # tên check bị fail, rỗng nếu pass hết
}
```

`build_freshness_report(df, settings, report_path) -> dict`:
```python
{
    "latest_published": str,
    "oldest_published": str,
    "stale_rows": int,     # age_days > settings.freshness_threshold_days
    "total_rows": int,
    "is_fresh": bool,
}
```

**Ai tạo:** Observability
**Ai tiêu thụ:** Reporting (2 hàm generate report markdown), Integration (in ra terminal / block pipeline nếu fail)

**Ràng buộc bắt buộc:**
- Ghi JSON report vào `settings.paths.quality_dir` (quality) và `settings.paths.freshness_report` (freshness).
- Report markdown (`generate_phase1_report`, `generate_corruption_report`) chỉ được điền số liệu đọc từ các dict trên — không hard-code giá trị.

---

## 3. Phân công 5 người

```
Ingestion ──▶ Cleaning ──┬──▶ Evaluation ──┐
                          └──▶ Observability ┴──▶ Integration (Pipeline + Corruption)
```

### Người 1 — Ingestion
**File sở hữu:** `src/ingestion/crossref.py`

**Việc cần làm:**
1. `parse_crossref_payload(payload)` — duyệt `payload["message"]["items"]`, map sang `PaperRecord` theo Contract A, bỏ record không hợp lệ (thiếu DOI/title).
2. `fetch_source_records(settings)` — gọi Crossref API với `source_query`, `source_filter`, `max_results`; có retry/backoff cho `429`/`503`; lưu raw response trước, parse sau, lưu raw records.
3. `load_raw_records(path)` — đọc lại JSON snapshot, map ngược thành `list[PaperRecord]` (dùng khi repair ở corruption flow).

**Definition of done:**
- [ ] `data/raw/crossref_response.json` và `data/raw/crossref_records.json` tồn tại sau khi chạy
- [ ] `paper_id` không trùng, trace được về DOI gốc
- [ ] Retry hoạt động khi giả lập lỗi 429/503 (test thủ công hoặc mock)

**Bàn giao cho:** Người 2 (list `PaperRecord`), Người 5 (đường dẫn raw để repair)

---

### Người 2 — Cleaning
**File sở hữu:** `src/ingestion/cleaning.py`

**Việc cần làm:**
1. `build_clean_dataframe(records, run_date)` theo đúng Contract B: normalize text, parse date, tính `age_days`, build `text_for_embedding`, dedupe, drop row xấu, sort.

**Definition of done:**
- [ ] `data/clean/papers_clean.csv` và `.json` tồn tại, đúng schema Contract B
- [ ] `paper_id` unique 100%
- [ ] Không có `text_for_embedding` rỗng
- [ ] Có log/print số row raw → clean và lý do bị loại

**Bàn giao cho:** Người 3, Người 4, Người 5 (clean dataframe)

---

### Người 3 — Evaluation
**File sở hữu:** `src/evaluation/testset.py`
**Cần đọc thêm (không sửa):** `src/evaluation/metrics.py`, `src/retrieval/qa.py`, `src/retrieval/index.py` — để biết `evaluate_pipeline` mong đợi field gì.

**Việc cần làm:**
1. `build_test_set(df, output_path)` theo Contract C: chọn paper đại diện, sinh câu hỏi 4 loại, ghi `ground_truth_doc_ids` từ `paper_id` thật.
2. Đọc thử vài row trong `test_set.json` để chắc chắn ID tồn tại trong clean data trước khi bàn giao.

**Definition of done:**
- [ ] `data/eval/test_set.json` tồn tại, đủ 4 loại câu hỏi
- [ ] Mọi `ground_truth_doc_ids` đều là `paper_id` có thật
- [ ] Sau khi Integration build xong index (Người 5), chạy thử `evaluate_pipeline` không lỗi field

**Bàn giao cho:** Người 5 (test set dùng trong `phase1.py` và `corruption_flow.py`)

---

### Người 4 — Observability
**File sở hữu:** `src/observability/quality.py`, `src/observability/reporting.py`

**Việc cần làm:**
1. `run_data_quality_checks(df, settings, report_name)` theo Contract D.
2. `build_freshness_report(df, settings, report_path)` theo Contract D.
3. `generate_phase1_report(...)` — markdown tổng hợp source summary + metrics + quality + freshness.
4. `generate_corruption_report(...)` — markdown so sánh baseline vs corrupted vs repaired (metrics + quality + freshness của từng trạng thái).

**Definition of done:**
- [ ] `data/quality/*.json` và `data/quality/freshness_report.json` tồn tại, đúng schema
- [ ] `data/reports/phase1_report.md` đọc được, số liệu khớp file JSON thật
- [ ] `data/reports/corruption_report.md` thể hiện rõ 3 cột baseline/corrupted/repaired

**Bàn giao cho:** Người 5 (gọi các hàm này trong pipeline)

---

### Người 5 — Integration / Pipeline (lead kỹ thuật)
**File sở hữu:** `src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`
**Cần hiểu rõ (không sửa, đã có sẵn code mẫu):** `src/retrieval/embeddings.py`, `index.py`, `agent.py`, `qa.py`, `src/retrieval/llm.py`

**Việc cần làm:**

1. **`corruption.py` → `corrupt_clean_dataframe(df, output_log_path)`**
   - Drop một số record mới nhất, blank summary, inject noise vào text, truncate title, làm `published` cũ đi, thêm duplicate rows, rebuild lại `text_for_embedding`.
   - Ghi log corruption (loại lỗi + số row bị ảnh hưởng) vào `output_log_path`.

2. **`phase1.py` → `main()`**
   - Load settings → fetch/load raw (Người 1) → clean (Người 2) → lưu clean → build Chroma index (`LocalEmbeddingIndex`) → tạo/load test set (Người 3) → `evaluate_pipeline` → quality + freshness (Người 4) → `generate_phase1_report` → (tuỳ chọn) demo agent trên vài câu hỏi.

3. **`corruption_flow.py` → `main()`**
   - Load baseline clean + metrics → corrupt → lưu corrupted artifacts (path riêng, KHÔNG ghi đè baseline) → rebuild index corrupted → evaluate → quality/freshness corrupted → repair lại từ raw (dùng `load_raw_records` của Người 1 + `build_clean_dataframe` của Người 2) → evaluate repaired → quality/freshness repaired → `generate_corruption_report`.

**Definition of done:**
- [ ] `uv run python script/run_phase1.py` chạy hết, sinh đủ artifact trong `data/clean`, `data/embeddings`, `data/eval`, `data/results`, `data/quality`, `data/reports`
- [ ] `uv run python script/run_corruption_flow.py` chạy sau baseline, không ghi đè baseline artifacts
- [ ] `data/results/corruption_log.json` và `data/reports/corruption_report.md` thể hiện rõ: corrupted làm giảm `retrieval_hit_rate`/`mean_token_f1`/`judge_accuracy`, repaired phục hồi lại gần baseline
- [ ] Giải thích được ít nhất 1 hit/miss cụ thể bằng artifact thật (không phải suy đoán)

---

## 4. Thứ tự & mốc kiểm tra (checkpoint)

| Mốc | Điều kiện để qua mốc | Ai chịu trách nhiệm chính |
|---|---|---|
| CP0 | Contract A–D đã chốt, mọi người hiểu field mình dùng/tạo | Cả team |
| CP1 | Raw ingestion chạy được, `PaperRecord` list hợp lệ | Người 1 |
| CP2 | Clean dataframe đúng schema, `paper_id` unique | Người 2 |
| CP3 | Test set + quality/freshness baseline sẵn sàng (song song) | Người 3, Người 4 |
| CP4 | `run_phase1.py` chạy end-to-end, có `baseline_metrics.json` | Người 5 |
| CP5 | `run_corruption_flow.py` chạy xong, có comparison report | Người 5 (dùng lại toàn bộ contract của 4 người kia) |

**Lưu ý:** Không ai chuyển sang bước sau khi bước trước còn lỗi contract (ví dụ: đừng build test set khi `paper_id` trong clean data chưa ổn định — sẽ phải làm lại).

## 5. Checklist nộp bài (đối chiếu `Rubric.md`)

- [ ] Code chia module rõ theo đúng 5 khu vực trên
- [ ] Raw / clean / embedding / eval / quality / report artifacts đầy đủ trong `data/`
- [ ] `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` đều tồn tại và có thể so sánh
- [ ] Báo cáo markdown khớp với artifact thực tế (không hard-code số)
- [ ] Không commit `.env` hoặc API key
- [ ] Đã đối chiếu `Rubric.md` cho từng mục (8 mục, 90 điểm cơ bản + bonus)
