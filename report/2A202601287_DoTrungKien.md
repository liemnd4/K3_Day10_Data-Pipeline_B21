# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đỗ Trung Kiên              |
| MSSV               | 2A202601287                |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | Group B21                  |
| Vai trò chính    | Ingestion Owner (Người 1)  |
| Repository         | https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21 |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Raw Ingestion & API Fetch | `src/ingestion/crossref.py`<br>- `fetch_source_records` | External API (`https://api.crossref.org/works`) & `Settings` | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` | Hoàn thành |
| Payload Parsing & Data Lineage | `src/ingestion/crossref.py`<br>- `parse_crossref_payload` | Raw JSON dictionary từ API response | List `PaperRecord` (Contract A) | Hoàn thành |
| Snapshot Loading (Repair Flow) | `src/ingestion/crossref.py`<br>- `load_raw_records` | Path `data/raw/crossref_records.json` | List `PaperRecord` khôi phục | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Xác minh Data Contract & Audit Completeness | Nguyễn Đình Liêm (Người 2 - Cleaning) | Đã audit 100% 24 record chứa đủ 11/11 trường theo Contract A, cung cấp Sample JSON record bàn giao cho bước Cleaning. |
| Kiểm thử tự động & Tích hợp Pipeline | Lê Trần Long (Người 5 - Lead kỹ thuật) | Tạo script kiểm thử độc lập luồng Ingestion đảm bảo `fetch_source_records` và `load_raw_records` hoạt động chính xác trước khi tích hợp vào `phase1.py` và `corruption_flow.py`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Gọi API thu thập dữ liệu học thuật | `src/ingestion/crossref.py`<br>`fetch_source_records` | Lấy thành công 24 bài báo chuẩn theo query & filter trong `Settings`. | `$env:PYTHONPATH="src"; uv run python -c "from ingestion.crossref import fetch_source_records; fetch_source_records(s)"` |
| Bảo lưu Raw API Response nguyên bản | `data/raw/crossref_response.json` | File 238 KB lưu toàn bộ HTTP payload thô từ Crossref API. | Kiểm tra file tồn tại và đúng cấu trúc Crossref response (`status`, `message.items`). |
| Parse & Lưu Raw Records Snapshot | `data/raw/crossref_records.json` | File 57.7 KB chứa 24 `PaperRecord` dạng phẳng đúng Contract A. | Kiểm tra schema 24 bản ghi với đầy đủ 11 trường dữ liệu. |
| Khôi phục từ snapshot | `src/ingestion/crossref.py`<br>`load_raw_records` | Đọc lại 24 `PaperRecord` chính xác từ file JSON snapshot. | `assert len(recs) == len(load_raw_records(path))` |

**Mô tả Output cụ thể tạo ra:**
- File `data/raw/crossref_response.json` (238 KB) lưu giữ chứng cứ nguyên bản từ nguồn Crossref API phục vụ Audit Lineage.
- File `data/raw/crossref_records.json` (57.7 KB) chứa 24 `PaperRecord` chuẩn hóa làm cầu nối bàn giao dữ liệu thô sạch cho module Cleaning và làm snapshot cho Repair Flow.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng module Ingestion có khả năng tự động thu thập metadata các công bố khoa học từ API công khai Crossref (`https://api.crossref.org/works`), đảm bảo:
1. Tạo được `paper_id` duy nhất và ổn định (stable key) từ DOI.
2. Trích xuất text và làm sạch các thẻ XML/JATS rác trong abstract.
3. Chống chịu được lỗi nghẽn mạng hoặc quá tải API (Rate limit `429` và Service Unavailable `503`).
4. Lưu trữ dữ liệu hai lớp (Dual-layer persistence) để phục vụ cả việc audit nguồn (Lineage) lẫn tái khôi phục dữ liệu ở Phase 2 (Repair Flow).

### Cách triển khai
- **Stable ID Generation:** Trích xuất DOI từ `item["DOI"]`, cắt bỏ toàn bộ tiền tố URL (`https://doi.org/`, `http://dx.doi.org/`) và trim khoảng trắng. `paper_id` này đóng vai trò là khóa nối xuyên suốt pipeline (Raw → Clean → Chroma Index → Evaluation).
- **Text Cleaning & Formatting:** Viết hàm `_clean_text` loại bỏ toàn bộ XML/JATS tags (`<jats:p>`, `<jats:title>`) bằng Regex, đồng thời giải mã ký tự HTML entities (`&amp;`, `&lt;`) bằng `html.unescape`.
- **Date Extraction:** Viết hàm `_extract_dates` hỗ trợ lấy ngày từ nhiều nguồn (`published-online`, `published-print`, `issued`, `created`), chuyển thành chuẩn ISO `YYYY-MM-DD`. Nếu thiếu ngày cập nhật (`updated`), gán fallback = `published`.
- **Retry Mechanism:** Thiết lập vòng lặp retry với **exponential backoff** (`wait_time = backoff_factor * (2 ** (attempt - 1))`) cho các mã lỗi HTTP `429` và `503` (tối đa 5 lần thử).

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| **Input** | `Settings` (chứa `source_query`, `source_filter`, `max_results`) & HTTP Response từ `https://api.crossref.org/works`. |
| **Output** | List `PaperRecord` dataclass & 2 file artifacts (`crossref_response.json`, `crossref_records.json`). |
| **Module phụ thuộc** | `src/core/config.py` (`Settings`, `Paths`). |
| **Module sử dụng output** | `src/ingestion/cleaning.py` (Người 2 - Cleaning) & `src/pipelines/corruption_flow.py` (Người 5 - Lead kỹ thuật). |
| **Điều kiện lỗi cần xử lý** | API nghẽn rate limit (HTTP 429/503), record thiếu DOI/Title (lọc bỏ), abstract chứa XML/JATS formatting. |

### Cách xác minh

```bash
$env:PYTHONPATH="src"
$env:PYTHONIOENCODING="utf-8"
uv run python -c "
from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records

s = load_settings()
records = fetch_source_records(s)
print(f'Fetched {len(records)} records.')
loaded = load_raw_records(s.paths.raw_records_json)
print(f'Loaded {len(loaded)} records.')
assert len(records) == len(loaded)
print('Sample paper_id:', records[0].paper_id)
"
```

- **Kết quả mong đợi:** Fetch được 24 records từ API, ghi 2 file vào `data/raw/`, load lại snapshot trả về đúng 24 records.
- **Kết quả thực tế:** Fetch và load thành công 24/24 records. `sample paper_id: 10.47576/2949-1894.2026.7.7.023`.
- **Artifact:** `data/raw/crossref_response.json` và `data/raw/crossref_records.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương án lưu trữ dữ liệu thô (raw data persistence) thu được từ Crossref API.
- **Các phương án đã cân nhắc:**
  - *Phương án 1:* Chỉ lưu duy nhất danh sách record sau khi đã parse (`crossref_records.json`).
  - *Phương án 2 (Được chọn):* Lưu hai lớp dữ liệu tách biệt: Dạng 1 (`crossref_response.json` - HTTP payload thô nguyên bản từ API) và Dạng 2 (`crossref_records.json` - danh sách phẳng `PaperRecord` đã parse).
- **Phương án đã chọn:** Phương án 2 (Dual-layer Persistence).
- **Lý do:**
  1. *Data Lineage & Audit:* Giữ lại `crossref_response.json` làm bằng chứng dữ liệu thô nguyên thủy từ nguồn, giúp đối chiếu xem dữ liệu lỗi do API Crossref trả về hay do logic parse của code.
  2. *Performance & Reproducibility:* Giữ lại `crossref_records.json` dạng snapshot phẳng giúp hàm `load_raw_records` khôi phục dữ liệu ở Phase 2 (Repair Flow) tức thì mà không cần gọi lại API nguồn.
- **Bằng chứng quyết định phù hợp:** Đã kiểm thử lưu thành công cả 2 file trong `data/raw/` với kích thước lần lượt là 238 KB (HTTP response gốc) và 57.7 KB (records snapshot).

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-7: character maps to <undefined>
  ```
  Và lỗi gián đoạn do HTTP status code `429 Too Many Requests` khi gọi API liên tục.
- **Lệnh hoặc bước tái hiện:**
  Chạy lệnh kiểm thử `uv run python -c "..."` trên terminal PowerShell Windows mặc định encoding CP1252 khi in các tiêu đề bài báo chứa ký tự Cyrillic/Tiếng Nga.
- **Nguyên nhân gốc:**
  - Terminal Windows PowerShell mặc định dùng bảng mã CP1252/ANSI không hỗ trợ in ký tự UTF-8 đa ngôn ngữ (tiếng Nga, tiếng Việt) từ API Crossref.
  - Crossref API áp dụng giới hạn Rate Limit (429) khi nhận nhiều request dồn dập.
- **Cách xử lý:**
  1. Thêm biến môi trường `$env:PYTHONIOENCODING="utf-8"` trước khi thực thi script trên Windows.
  2. Thiết lập cơ chế **exponential backoff retry** trong `fetch_source_records`: khi gặp lỗi `429` hoặc `503`, chương trình sẽ tự động tạm dừng `wait_time = backoff_factor * (2 ** (attempt - 1))` giây trước khi thử lại.
- **Cách xác minh sau khi sửa:**
  Chạy lại lệnh test với `PYTHONIOENCODING="utf-8"`, lệnh thực thi mượt mà, trả về kết quả `SUCCESSFUL` và không còn bị crash terminal.
- **Bài học kỹ thuật:**
  Luôn chú ý đến Encoding khi xử lý dữ liệu text đa ngôn ngữ trên hệ điều hành Windows và thiết lập cơ chế retry/backoff cho mọi lệnh gọi External Web API.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô từ Crossref API được `fetch_source_records` lấy về và lưu vào `data/raw/`. Tiếp theo, module Cleaning (`cleaning.py`) đọc raw records, làm sạch text, tính toán `age_days` và ghép thành chuỗi `text_for_embedding` rồi xuất ra `data/clean/papers_clean.csv`. Module Embedding (`index.py`) đọc file clean, chạy mô hình `sentence-transformers/all-MiniLM-L6-v2` chuyển văn bản thành vector embeddings và lưu vào Vector Store ChromaDB (`data/chroma`).

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Evaluation set (`test_set.json`) gồm 60 câu hỏi được tạo ra bằng cách trích xuất thông tin tiêu biểu từ dataset sạch (`summary`, `authors`, `date`, `categories`). Mỗi câu hỏi đính kèm danh sách `ground_truth_doc_ids` (chính là `paper_id` của bài báo chứa đáp án). Khi đánh giá, module evaluation cho agent thực hiện Semantic Search tìm ra top-k bài báo; nếu `paper_id` thật nằm trong kết quả tìm được thì tính là 1 Hit (`retrieval_hit_rate`). Đồng thời, câu trả lời do LLM sinh ra được so sánh với `ground_truth` để tính `mean_token_f1` và `judge_accuracy`.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - *Quality checks* tập trung vào tính toàn vẹn và tính đúng đắn của cấu trúc dữ liệu (Data Structure & Integrity) tại thời điểm hiện tại: kiểm tra xem có row nào bị null `paper_id`, trùng lặp ID, rỗng title, hay summary quá ngắn hay không.
   - *Freshness monitoring* tập trung vào tính cập nhật theo thời gian (Data Timeliness): đo đạc khoảng cách ngày xuất bản `published` so với ngày hiện tại (`age_days`), xác định xem dữ liệu có bị lỗi thời (stale) so với ngưỡng quy định `freshness_threshold_days` (180 ngày) hay không.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Sử dụng chung một bộ `test_set.json` cố định xuyên suốt cả 3 trạng thái là nguyên tắc quan trọng để đảm bảo tính chuẩn xác của thực nghiệm (Controlled Experiment). Việc này giữ nguyên biến số đầu vào (cùng 60 câu hỏi và đáp án chuẩn), giúp ta đo lường chính xác sự biến động chỉ số (metrics) hoàn toàn do sự suy giảm chất lượng dữ liệu (Corruption) và sự phục hồi chất lượng dữ liệu (Repair) gây ra.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair được xem là thành công khi:
   - *Artifacts:* File `data/clean/papers_clean_repaired.csv` được khôi phục đầy đủ từ raw source snapshot, file `data/quality/freshness_report.json` khôi phục về trạng thái `is_fresh: true`, và `data/reports/corruption_report.md` thể hiện rõ cả 3 cột dữ liệu.
   - *Metrics:* Các chỉ số đánh giá `retrieval_hit_rate` (tăng từ 0.8 lên 1.0), `mean_token_f1` (tăng từ 0.6565 lên 0.9000), và `judge_accuracy` (tăng từ 0.6167 lên 0.8667) của trạng thái Repaired tăng bật trở lại hoàn toàn tương đương với mức Baseline ban đầu.

---

## 8. Phân tích kết quả

### Metrics chính (Đã cập nhật từ thực nghiệm `Group B21`)

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8000 |   1.0000 | Search Hit Rate suy giảm khi bị drop 3 bài báo và chèn nhiễu, khôi phục hoàn toàn khi Repair từ raw. |
| `mean_token_f1`      |   0.9000 |    0.6565 |   0.9000 | Token F1 giảm mạnh do Agent sinh câu trả lời dựa trên abstract rỗng/nhiễu, phục hồi về 0.9000 sau repair. |
| `judge_accuracy`     |   0.8667 |    0.6167 |   0.8667 | Tỉ lệ câu trả lời đúng do LLM Judge đánh giá bị tụt ở Corrupted, phục hồi hoàn toàn sau Repair. |
| `mean_judge_score`   |   4.4667 |    3.6000 |   4.4833 | Điểm trung bình đánh giá từ LLM Judge giảm xuống 3.60/5 và phục hồi lên 4.48/5. |
| Quality checks         |     PASS |      FAIL |     PASS | Báo cáo Quality chuyển FAIL khi bị rỗng summary và trùng lặp row, PASS trở lại sau Repair. |
| Freshness status       |    FRESH |     STALE |    FRESH | Freshness chuyển STALE khi dữ liệu bị đổi ngày về 1990, FRESH trở lại sau Repair. |

### Kết luận từ số liệu

1. **Chuỗi Nhân quả 1 (Corruption Impact):**  
   `Bơm dữ liệu lỗi (trùng lặp, rỗng abstract, ngày xuất bản cổ xưa 1990)` $\longrightarrow$ `Kích hoạt cảnh báo Quality FAIL & Freshness STALE` $\longrightarrow$ `Làm Hit Rate giảm từ 1.0 xuống 0.8, Token F1 giảm từ 0.9000 xuống 0.6565 và Judge Score giảm từ 4.47 xuống 3.60`.

2. **Chuỗi Nhân quả 2 (Repair Recovery):**  
   `Khôi phục dữ liệu từ Raw Snapshot (crossref_records.json)` $\longrightarrow$ `Khôi phục tín hiệu chất lượng (Quality PASS, Freshness FRESH)` $\longrightarrow$ `Đưa toàn bộ hiệu năng RAG Agent (Hit Rate 1.0, Token F1 0.9, Judge Accuracy 0.8667) trở lại hoàn toàn tương đương với baseline ban đầu`.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Xây dựng Data Pipeline cần tuân thủ nghiêm ngặt **Data Contract** và lưu trữ dữ liệu thô hai lớp (Raw HTTP Payload & Parsed Snapshot) để đảm bảo tính an toàn, khả năng audit và khả năng phục hồi dữ liệu khi gặp sự cố.
2. **Về Data Quality & Observability:** Chất lượng dữ liệu đầu vào quyết định trực tiếp hiệu năng của hệ thống RAG (*Garbage In, Garbage Out*). Việc giám sát tự động các chỉ số Data Quality & Freshness giúp phát hiện sớm các bất thường dữ liệu trước khi ảnh hưởng tới người dùng.
3. **Về ảnh hưởng của Data tới RAG Agent:** Một rủi ro nhỏ trong khâu Ingestion (như lọt thẻ XML rác, mất title hoặc sai định dạng ngày) có thể làm giảm mạnh điểm Retrieval Hit Rate và khiến LLM đưa ra câu trả lời sai lệch (hallucination).

### Nếu có thêm thời gian

Nếu có thêm thời gian, em sẽ triển khai thêm cơ chế **Streaming / Pagination Fetching** cho Crossref API để hỗ trợ lấy hàng ngàn bài báo với nhiều luồng xử lý bất đồng bộ (`asyncio` / `aiohttp`), kết hợp tự động phát hiện mã hóa ngôn ngữ (encoding auto-detection) để xử lý hoàn hảo mọi ký tự đặc biệt từ các nguồn tạp chí quốc tế.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Trung Kiên  
**Ngày xác nhận:** 2026-08-06
