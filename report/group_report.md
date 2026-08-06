# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K3              |
| Tên nhóm         | Group B21     |
| Repository         | https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21 |
| Ngày hoàn thành | 2026-08-06               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đỗ Trung Kiên | 2A202601287 | Ingestion Owner (Người 1) | `src/ingestion/crossref.py`, `data/raw/` |
| 2 | Nguyễn Đình Liêm | 2A202601421 | Cleaning Owner (Người 2) | `src/ingestion/cleaning.py`, `data/clean/` |
| 3 | Nguyễn Văn Hưng | 2A202601970 | Evaluation Owner (Người 3) | `src/evaluation/testset.py`, `data/eval/` |
| 4 | Nguyễn Hồng Yến | 2A202601065 | Observability Owner (Người 4) | `src/observability/quality.py`, `src/observability/reporting.py`, `data/quality/`, `data/reports/phase1_report.md` |
| 5 | Lê Trần Long | 2A202601257 | Pipeline Integrator / Lead kỹ thuật (Người 5) | `src/ingestion/corruption.py`, `src/pipelines/`, `data/results/corruption_log.json`, `data/reports/corruption_report.md` |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

Nhóm đã hoàn thành toàn bộ các thành phần của data pipeline và data observability. Ingestion đã được cài đặt để gọi API Crossref và lưu snapshot raw. Cleaning đã thực hiện chuẩn hóa text, lọc bản ghi trùng lặp và tính độ tươi mới. Evaluation set gồm 60 câu hỏi đã được tạo ra tự động từ các bài viết thực tế. Chúng tôi đã mô phỏng các lỗi dữ liệu thực tế (bỏ bài viết mới nhất, xóa tóm tắt, chèn nhiễu, cắt tiêu đề, đổi ngày xuất bản cổ xưa và nhân bản trùng dòng). Kết quả cho thấy dữ liệu lỗi làm giảm Hit Rate từ 1.0 xuống 0.8 và Token F1 từ 0.9 xuống 0.6565. Hệ thống Observability đã phát hiện chính xác các lỗi này (báo FAIL và STALE). Quy trình Repair đã tải lại dữ liệu thô và làm sạch lại để khôi phục hoàn toàn hiệu năng RAG.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API | Gọi API, parse thành PaperRecord, hỗ trợ retry/backoff | `data/raw/` | Đỗ Trung Kiên |
| Cleaning          | Raw records | Normalize text, parse dates, deduplicate, filter short text | `data/clean/` | Nguyễn Đình Liêm |
| Embedding/index   | Cleaned DataFrame | MiniLM-L6-v2 embedding model, Chroma DB index | `data/embeddings/` | Lê Trần Long |
| Evaluation        | Cleaned DataFrame | Tạo test set (summary, authors, date, categories) | `data/eval/` | Nguyễn Văn Hưng |
| Observability     | Cleaned/Corrupted DataFrame | Kiểm tra chất lượng dữ liệu và độ tươi mới | `data/quality/` | Nguyễn Hồng Yến |
| Corruption/repair | Cleaned DataFrame | Mô phỏng lỗi dữ liệu và khôi phục từ nguồn thô | `data/clean/` | Lê Trần Long |
| Orchestration     | Settings & Data paths | Tích hợp baseline pipeline & corruption comparison flow | `data/reports/` | Lê Trần Long |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openai`         |
| `LLM_MODEL`                | `gpt-4o-mini`         |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2`         |
| Số lượng Crossref records | `24`         |
| Retrieval`top_k`           | `4`         |
| Freshness threshold          | `180 days`         |
| Random seed, nếu có        | `None`         |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-08-06 10:34 | [`data/reports/phase1_report.md`](file:///d:/AI_ThucChien_Lab/Lab10/data/reports/phase1_report.md) |
| Corruption flow   | Thành công | 2026-08-06 10:43 | [`data/reports/corruption_report.md`](file:///d:/AI_ThucChien_Lab/Lab10/data/reports/corruption_report.md) |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --------------------------- | ------------------------------------- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | Query: `"agentic retrieval augmented generation large language model"`<br>Filter: `"from-pub-date:<180_days_ago>,has-abstract:true"` |
| Thời điểm lấy dữ liệu | 2026-08-06T03:02:37Z |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Exponential Backoff Retry (sleep `wait_time = backoff_factor * (2 ** (attempt - 1))`) cho mã lỗi HTTP `429` (Rate limit) và `503` (Service unavailable), tối đa 5 lần thử. |

### Raw và clean schema (Contract A & Contract B)

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | `str` | Có | Stable DOI identifier (đã cắt bớt `https://doi.org/`) | Loại bỏ record nếu thiếu DOI |
| `title` | `str` | Có | Tiêu đề công bố khoa học | Loại bỏ record nếu rỗng title |
| `summary` | `str` | Không | Abstract/tóm tắt nội dung (đã làm sạch XML/JATS tags) | Fallback `""` nếu thiếu |
| `authors` | `list[str]` | Không | Danh sách tên các tác giả | Fallback `[]` nếu thiếu |
| `categories` | `list[str]` | Không | Danh mục/chủ đề nghiên cứu | Fallback `[]` nếu thiếu |
| `primary_category` | `str` | Không | Danh mục chính (`categories[0]`) | Fallback `""` nếu thiếu |
| `published` | `str` | Có | Ngày công bố dạng ISO `YYYY-MM-DD` | Fallback `"1970-01-01"` |
| `updated` | `str` | Có | Ngày cập nhật dạng ISO `YYYY-MM-DD` | Fallback = `published` nếu thiếu |
| `abs_url` | `str` | Có | Đường dẫn trang thông tin bài báo | Fallback `https://doi.org/{paper_id}` |
| `pdf_url` | `str` | Không | Đường dẫn tải PDF | Fallback `""` nếu thiếu |
| `comment` | `str` | Không | Thông tin nhà xuất bản / loại hình | Fallback `""` nếu thiếu |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại bỏ record không có DOI hoặc Title | Completeness / Validity | 0 (API trả về đủ 24 bài hợp lệ) | Audit script đối chiếu `crossref_response.json` vs `crossref_records.json` |
| Bóc tách XML/JATS tags trong abstract | Conformity / Accuracy | 24 | Regex strip `<[^>]+>` và `html.unescape` |
| Deduplicate theo `paper_id` | Uniqueness | 0 | `seen_paper_ids` set check |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding` được tạo bằng cách ghép: Title + Summary + Categories.
- Document ID (`paper_id`) chính là DOI của bài báo đã chuẩn hóa (loại bỏ tiền tố URL).
- `age_days` được tính bằng hiệu số ngày giữa `run_date` và `published` date (ngày công bố).

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | `60`                 |
| Các`question_type`                    | `summary, authors, date, categories`                  |
| Ground-truth document ID                 | Đối chiếu với `paper_id` thực tế trong cleaned DataFrame |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2`                  |
| Vector store/collection                  | Chroma DB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval`top_k`                       | `4`                   |
| LLM provider/model                       | `openai/gpt-4o-mini`                   |
| Test set dùng chung cho ba trạng thái | [`data/eval/test_set.json`](file:///d:/AI_ThucChien_Lab/Lab10/data/eval/test_set.json) |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Việc giữ nguyên test set cố định xuyên suốt ba trạng thái nhằm đảm bảo tính khách quan và nhất quán trong việc đo đạc hiệu năng. Bằng cách giữ nguyên các câu hỏi và ground truth, bất kỳ sự thay đổi nào về điểm số (Hit Rate, F1, Judge Score) đều phản ánh chính xác chất lượng của cơ sở dữ liệu (sạch vs lỗi vs sửa đổi) và chất lượng index, loại bỏ sai số do tập câu hỏi thay đổi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | Chứa phản hồi thô và record đã parse |
| Cleaned dataset          | `data/clean/`                        | Có | Chứa CSV và JSON sạch |
| Embedding manifest/index | `data/embeddings/`                   | Có | Chứa manifest lưu thông tin collection |
| Evaluation set           | `data/eval/`                         | Có | Chứa tập câu hỏi test_set.json |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Chứa điểm số RAG baseline |
| Quality/freshness        | `data/quality/`                      | Có | Chứa báo cáo chất lượng & độ tươi mới |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Báo cáo Baseline Markdown hoàn chỉnh |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     `1.0000` | 100% tài liệu chính xác được tìm thấy thành công |
| `mean_token_f1`      |     `0.9000` | Độ trùng khớp từ vựng của câu trả lời đạt mức xuất sắc |
| `judge_accuracy`     |     `0.8667` | Tỉ lệ câu trả lời hoàn toàn chính xác được LLM Judge công nhận |
| `mean_judge_score`   |     `4.4667` | Điểm đánh giá trung bình từ LLM Judge đạt 4.47/5 |
| Ragas, nếu có        | `N/A` | Bị bỏ qua do `RUN_RAGAS=0` để tăng tốc độ chạy |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `paper_id_null_check` | Completeness | 0 null | Pass (0 null) | `baseline_quality.json` |
| `paper_id_duplicate_check` | Uniqueness | 0 duplicate | Pass (0 duplicate) | `baseline_quality.json` |
| `title_null_check` | Validity | 0 null | Pass (0 null) | `baseline_quality.json` |
| `summary_short_check` | Conformity | 0 short (<20 chars) | Pass (0 short) | `baseline_quality.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | `data/clean/papers_clean.csv`            |
| Timestamp mới nhất       | `2026-08-05`                         |
| Ngưỡng freshness         | `180 days`                         |
| Trạng thái baseline      | `FRESH`               |
| Lý do                     | Không có bài báo nào có tuổi đời vượt quá 180 ngày so với run_date |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Dropped latest | Bỏ 3 bài báo mới nhất | 3 | Hit Rate giảm | `corrupted_metrics.json` | Reload từ raw records và clean lại |
| Blank summary | Xóa tóm tắt của 2 dòng | 2 | Check quality FAIL | `corrupted_quality.json` | Reload từ raw records và clean lại |
| Noise summary | Chèn chuỗi lỗi vào abstract | 2 | F1 & Judge score giảm | `corrupted_metrics.json` | Reload từ raw và clean lại |
| Truncate title | Cắt tiêu đề còn 5 ký tự | 2 | Exact Lookup match lỗi | `corrupted_answers.json` | Reload từ raw và clean lại |
| Stale dates | Đổi ngày về năm 1990 | 2 | Freshness STALE | `freshness_report_corrupted.json` | Reload từ raw và clean lại |
| Duplicate records | Nhân bản 2 dòng bất kỳ | 2 | Check quality FAIL | `corrupted_quality.json` | Reload từ raw và clean lại |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi nhận đầy đủ 6 loại lỗi dữ liệu, liệt kê chính xác số dòng bị tác động cho từng loại.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Việc giữ nguyên test set cố định xuyên suốt ba trạng thái nhằm đảm bảo tính khách quan và nhất quán trong việc đo đạc hiệu năng. Bằng cách giữ nguyên các câu hỏi và ground truth, bất kỳ sự thay đổi nào về điểm số (Hit Rate, F1, Judge Score) đều phản ánh chính xác chất lượng của cơ sở dữ liệu (sạch vs lỗi vs sửa đổi) và chất lượng index, loại bỏ sai số do tập câu hỏi thay đổi.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |   1.0000 |    0.8000 |   1.0000 |                  -0.2000 |         +0.2000 | Retrieval sụt giảm khi bị drop 3 bài báo và chèn nhiễu, khôi phục hoàn toàn khi repair |
| `mean_token_f1`        |   0.9000 |    0.6565 |   0.9000 |                  -0.2435 |         +0.2435 | F1 giảm mạnh do Agent sinh câu trả lời dựa trên tóm tắt trống hoặc nhiễu |
| `judge_accuracy`       |   0.8667 |    0.6167 |   0.8667 |                  -0.2500 |         +0.2500 | Tỉ lệ đúng do Judge đánh giá giảm đáng kể khi dữ liệu bị lỗi |
| `mean_judge_score`     |   4.4667 |    3.6000 |   4.4833 |                  -0.8667 |         +0.8833 | Điểm trung bình giảm xuống 3.60 và phục hồi hoàn toàn lên 4.48 |
| Quality checks pass/fail |     PASS |      FAIL |     PASS |                     FAIL |            PASS | Báo cáo quality báo lỗi trùng lặp và summary ngắn |
| Freshness status         |    FRESH |     STALE |    FRESH |                    STALE |           FRESH | Báo cáo freshness báo lỗi dữ liệu cũ từ năm 1990 |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Bơm dữ liệu lỗi (trùng lặp, rỗng abstract, ngày xuất bản cũ)] → [Kích hoạt cảnh báo Quality FAIL & Freshness STALE] → [Làm Hit Rate giảm từ 1.0 xuống 0.8 và Token F1 giảm từ 0.9 xuống 0.6565].
2. [Khôi phục dữ liệu từ raw snapshot] → [Khôi phục chất lượng dữ liệu (Quality PASS, Freshness FRESH)] → [Đưa hiệu năng RAG Agent trở lại hoàn toàn tương đương với baseline ban đầu].

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** Gặp lỗi `KeyError: 'categories_joined'` trong file `metrics.py` khi chạy đánh giá trên dữ liệu corrupted.
- **Nguyên nhân:** Khi lưu DataFrame corrupted thành CSV và load lại, các ô trống trong các cột string (như categories_joined) được pandas đọc lên dưới dạng float `NaN`. Khi gửi vào Chroma, ChromaDB tự động loại bỏ các key có giá trị `NaN` khỏi metadata, dẫn tới thiếu key này.
- **Cách xử lý:** Sửa hàm `_build_documents` trong `retrieval/index.py` để gọi `df = df.fillna("")` trước khi tạo metadata, đảm bảo mọi giá trị `NaN` được đưa về chuỗi rỗng hợp lệ.
- **Cách xác minh:** Chạy lại `uv run python script/run_corruption_flow.py` thành công không còn lỗi KeyError.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Tập dữ liệu nhỏ (24 bài báo) và test set 60 câu hỏi | Chưa đánh giá hết hiệu năng tìm kiếm ở quy mô lớn | Mở rộng `max_results` lên 100+ trong Settings |
| Các câu hỏi test set sinh theo template heuristic cố định | Chưa đánh giá được tính đa dạng ngôn ngữ và độ phức tạp của câu hỏi thực tế | Sử dụng LLM sinh bộ test set (như Ragas Testset Generator) đa dạng hơn |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
