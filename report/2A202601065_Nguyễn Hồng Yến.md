# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| ------------------ | -------------------------- |
| Họ và tên | Nguyễn Hồng Yến |
| MSSV | 2A202601065 |
| Khóa/Lớp | K3 |
| Tên nhóm | Nhóm B21 |
| Vai trò chính | Người 4 — Observability (Quality, Freshness & Reporting) |
| Repository | https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21 |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Quality Check | `src/observability/quality.py`<br>- `run_data_quality_checks` | `df` (Clean DataFrame), `settings`, `report_name` | `data/quality/{report_name}_quality.json` (Contract D) | Hoàn thành |
| Freshness Monitoring | `src/observability/quality.py`<br>- `build_freshness_report` | `df` (Clean DataFrame), `settings`, `report_path` | `data/quality/freshness_report.json` (Contract D) | Hoàn thành |
| Baseline Report Generator | `src/observability/reporting.py`<br>- `generate_phase1_report` | `source_summary`, `metrics`, `quality`, `freshness` | `data/reports/phase1_report.md` (Contract D) | Hoàn thành |
| Corruption Comparison Report | `src/observability/reporting.py`<br>- `generate_corruption_report` | Baseline, Corrupted & Repaired metrics/quality/freshness | `data/reports/corruption_report.md` (Contract D) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Xây dựng UI Observability Dashboard | Cả nhóm & Giám khảo thuyết trình | Tạo ứng dụng Streamlit (`app.py`) trực quan hóa 6 Tab bao gồm sơ đồ luồng dữ liệu 2 pha, KPI cards, bảng so sánh metrics, chất lượng dữ liệu và trình so sánh câu trả lời RAG. |
| Kiểm thử an toàn định dạng dữ liệu (Defensive extraction) | Người 5 (Integration) | Bọc lót các helper extraction safe (`.get()`, `errors="coerce"`) để pipeline không bao giờ bị crash kể cả khi dữ liệu bị lỗi mạnh. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Thực thi kiểm định Data Quality | `src/observability/quality.py`<br>`run_data_quality_checks` | Xuất `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`. | Kiểm tra file JSON trong `data/quality/`, phát hiện chính xác 2 lỗi ngầm ở pha Corrupted. |
| Giám sát độ mới dữ liệu (Freshness) | `src/observability/quality.py`<br>`build_freshness_report` | Xuất `freshness_report.json` định kỳ theo `freshness_threshold_days`. | Kiểm tra cờ `is_fresh` (False ở Corrupted khi có 2 bài báo quá 180 ngày). |
| Sinh báo cáo Markdown Pha 1 | `src/observability/reporting.py`<br>`generate_phase1_report` | `data/reports/phase1_report.md` | Đọc file Markdown, kiểm tra số liệu khớp 100% với file JSON thực tế. |
| Sinh báo cáo So sánh 3 Pha | `src/observability/reporting.py`<br>`generate_corruption_report` | `data/reports/corruption_report.md` | Kiểm tra bảng 6 cột thể hiện rõ Impact Delta và Recovery Delta của 4 chỉ số RAG. |

**Mô tả Output cụ thể tạo ra:**
- Các file JSON trong `data/quality/`: `baseline_quality.json`, `corrupted_quality.json`, `repaired_quality.json`, `freshness_report.json`.
- Các file Markdown trong `data/reports/`: `phase1_report.md` và `corruption_report.md`.
- Giao diện Dashboard UI `app.py` chạy bằng Streamlit để thuyết trình dự án.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng hệ thống Data Observability tự động nhằm:
1. Phát hiện sớm các lỗi ngầm dữ liệu (Zero Silent Failure) như trùng lặp `paper_id`, tóm tắt rỗng (`summary`), hay bài báo quá cũ trước khi nạp vào Vector Database.
2. Định lượng chính xác tác động của dữ liệu lỗi lên độ chính xác của RAG Agent (từ Retrieval Hit Rate đến LLM Judge Accuracy).
3. Đánh giá tính hiệu quả của cơ chế Data Repair khi phục hồi từ Raw Snapshot.
4. Tự động biên soạn báo cáo chuẩn Markdown phục vụ audit và thuyết trình.

### Cách triển khai
- **Quality Checks Logic (`quality.py`):** Viết hàm `run_data_quality_checks` đếm số lượng `paper_id_null`, `paper_id_duplicate`, `title_null`, và `summary_short` (< 20 ký tự). Đánh giá cổng chất lượng `checks_passed = (len(failures) == 0)`.
- **Freshness Calculation (`quality.py`):** Viết hàm `build_freshness_report` ép kiểu ngày tháng dạng ISO `YYYY-MM-DD`, tính số tuổi bài báo `age_days` so với `run_date` và so sánh với ngưỡng `freshness_threshold_days` (180 ngày).
- **Dynamic Markdown Generation (`reporting.py`):** 
  - Hàm `generate_phase1_report` tự động chuyển đổi thông tin nguồn ingestion, chỉ số đánh giá RAG, kết quả quality check và freshness thành file báo cáo Markdown chuẩn.
  - Hàm `generate_corruption_report` tự động tính toán các hằng số chênh lệch:
    - $\text{Impact Delta} = \text{Metric}_{\text{Corrupted}} - \text{Metric}_{\text{Baseline}}$
    - $\text{Recovery Delta} = \text{Metric}_{\text{Repaired}} - \text{Metric}_{\text{Corrupted}}$
    và dựng bảng so sánh 6 cột trực quan.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| **Input** | `df` (DataFrame từ bước Cleaning), `Settings`, các file `metrics.json` từ bước Evaluation. |
| **Output** | Danh sách file JSON trong `data/quality/` và báo cáo Markdown trong `data/reports/`. |
| **Module phụ thuộc** | `src/core/config.py` (`Settings`, `Paths`). |
| **Module sử dụng output** | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` (Người 5) & Thuyết trình nhóm. |
| **Điều kiện lỗi cần xử lý** | Khung dữ liệu DataFrame bị thiếu cột, các key trong JSON metrics bị lệch tên giữa các thành viên, dữ liệu rỗng. |

### Cách xác minh

```bash
uv run python -c "
import json
from pathlib import Path

# Kiểm tra sự tồn tại của các file artifact do Observability tạo ra
quality_files = ['baseline_quality.json', 'corrupted_quality.json', 'repaired_quality.json', 'freshness_report.json']
for f in quality_files:
    p = Path('data/quality') / f
    assert p.exists(), f'Thiếu file {f}'
    print(f'✅ Found quality artifact: {f}')

reports = ['phase1_report.md', 'corruption_report.md']
for r in reports:
    p = Path('data/reports') / r
    assert p.exists(), f'Thiếu file {r}'
    print(f'✅ Found report artifact: {r}')
"
```

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cách thức trích xuất dữ liệu từ dictionary `metrics` và `quality` để sinh báo cáo Markdown trong `reporting.py`.
- **Các phương án đã cân nhắc:**
  - *Phương án 1:* Đọc cứng tên key (Hardcoded key access như `metrics["retrieval_hit_rate"]`).
  - *Phương án 2 (Được chọn):* Sử dụng cơ chế bọc lót trích xuất an toàn (Defensive Extraction) bằng cách duyệt fallback nhiều tên key tương đương (như `metrics.get("retrieval_hit_rate", metrics.get("hit_rate", 0.0))`) và ép kiểu số `float` an toàn.
- **Phương án đã chọn:** Phương án 2 (Defensive Extraction).
- **Lý do:** Trong quá trình làm việc nhóm, module Evaluation của thành viên khác có thể đổi nhẹ tên key hoặc trả về dạng string. Việc dùng Defensive Extraction giúp module Observability không bao giờ bị nổ lỗi (`KeyError` hoặc `TypeError`) giữa chừng, đảm bảo toàn bộ pipeline 5 người vận hành mượt mà.
- **Bằng chứng quyết định phù hợp:** Pipeline chạy End-to-End thành công 100%, sinh ra báo cáo Markdown chính xác mà không gặp bất kỳ lỗi gián đoạn nào.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  AttributeError: 'Styler' object has no attribute 'applymap'
  ```
  Xuất hiện khi chạy Dashboard UI Streamlit hiển thị bảng so sánh 3 pha.
- **Lệnh hoặc bước tái hiện:**
  Chạy lệnh `uv run streamlit run app.py` trên môi trường Python 3.12 cài đặt thư viện Pandas mới (`pandas >= 2.1.0`).
- **Nguyên nhân gốc:**
  Pandas phiên bản 2.1.0 trở lên đã chính thức loại bỏ phương thức `Styler.applymap()` và thay thế bằng `Styler.map()`.
- **Cách xử lý:**
  Cập nhật toàn bộ các cuộc gọi hàm định dạng bảng màu trong `app.py` từ `applymap()` sang `map()`.
- **Cách xác minh sau khi sửa:**
  Chạy lại Streamlit Dashboard, giao diện tải thành công 100%, các bảng so sánh hiển thị màu đỏ/xanh chuẩn xác theo chênh lệch chỉ số.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Dữ liệu thô từ Crossref API được Người 1 lấy về và lưu vào `data/raw/`. Module Cleaning (Người 2) đọc raw records, làm sạch text, tính toán `age_days` và ghép thành chuỗi `text_for_embedding` rồi xuất ra `data/clean/papers_clean.csv`. Module Embedding & Indexing (Người 3) đọc file clean, sử dụng mô hình `sentence-transformers/all-MiniLM-L6-v2` mã hóa văn bản thành vector embeddings và lưu vào Vector Database ChromaDB (`data/chroma`).

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Evaluation set (`test_set.json`) chứa 60 mẫu câu hỏi kèm đáp án `ground_truth` và danh sách bài báo chứa câu trả lời `ground_truth_doc_ids`. Khi đánh giá, RAG Agent thực hiện Semantic Search để tìm top-k bài báo; nếu `paper_id` thật nằm trong kết quả tìm được thì đếm là 1 Hit (`retrieval_hit_rate`). Đồng thời câu trả lời do LLM trả về được so sánh với `ground_truth` để tính `mean_token_f1` và `judge_accuracy`.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   - *Quality checks* tập trung vào tính toàn vẹn và đúng đắn của cấu trúc dữ liệu (Integrity) tại thời điểm hiện tại: kiểm tra dòng bị null `paper_id`, trùng lặp ID, rỗng title, hay summary quá ngắn (<20 ký tự).
   - *Freshness monitoring* tập trung vào tính cập nhật theo thời gian (Timeliness): đo khoảng cách ngày xuất bản `published` so với ngày hiện tại (`age_days`), xác định dữ liệu có bị cũ (stale) so với ngưỡng quy định `freshness_threshold_days` (180 ngày) hay không.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Sử dụng chung một bộ `test_set.json` cố định xuyên suốt cả 3 trạng thái là nguyên tắc thí nghiệm đối chứng (Controlled Experiment). Việc này giúp cố định biến số đầu vào (cùng bộ câu hỏi và đáp án chuẩn), đảm bảo sự biến động của các chỉ số hoàn toàn do sự suy giảm chất lượng dữ liệu (Corruption) và sự phục hồi chất lượng dữ liệu (Repair) gây ra.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repair được xem là thành công khi:
   - *Artifacts:* `papers_clean_repaired.csv` khôi phục hoàn toàn từ raw snapshot, `repaired_quality.json` và `freshness_report_repaired.json` đạt trạng thái `checks_passed: true` và `is_fresh: true`, đồng thời `corruption_report.md` thể hiện rõ số liệu 3 cột.
   - *Metrics:* Các chỉ số `retrieval_hit_rate` (phục hồi từ 80% lên 100%), `mean_token_f1` (từ 0.6565 lên 0.9000), và `judge_accuracy` (từ 61.67% lên 86.67%) bật trở lại bằng mức Baseline ban đầu.

---

## 8. Phân tích kết quả thực tế

### Bảng kết quả thực nghiệm 60 mẫu test (Real Metrics)

| Metric / Signal | Baseline (Clean) | Corrupted (Khi bị lỗi) | Repaired (Phục hồi) | Nhận xét cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | **1.0000** | **0.8000** | **1.0000** | Giảm 20% ở pha Corrupted và phục hồi 100% sau khi Repair. |
| `mean_token_f1` | **0.9000** | **0.6565** | **0.9000** | Sụt giảm mạnh 0.2435 do RAG đọc phải context rác/bị hỏng. |
| `judge_accuracy` | **0.8667** | **0.6167** | **0.8667** | Độ chính xác LLM Judge giảm 25% ở pha Corrupted. |
| `mean_judge_score` | **4.4667** | **3.6000** | **4.4833** | Điểm trung bình sụt từ 4.47 xuống 3.60/5.0. |
| Quality checks status | **PASS** | **FAIL** | **PASS** | Phát hiện chính xác 2 lỗi ngầm trùng ID và summary ngắn ở pha Corrupted. |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Báo STALE ở pha Corrupted (2 bài quá 180 ngày) và FRESH trở lại sau Repair. |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Chất lượng dữ liệu quyết định chất lượng AI (*Garbage In, Garbage Out*):** Chỉ một vài lỗi nhỏ như trùng lặp ID hay summary quá ngắn đã làm giảm 20% khả năng truy xuất và 25% độ chính xác của LLM Agent.
2. **Tầm quan trọng của Observability Gate:** Giám sát tự động giúp phát hiện sớm các lỗi ngầm trước khi dữ liệu độc hại được đưa vào Vector Database, loại bỏ hoàn toàn rủi ro Zero Silent Failure.
3. **Quy trình Phục hồi dữ liệu (Data Repair Lineage):** Không bao giờ sửa dữ liệu trực tiếp trên file bị hỏng mà phải rollback về Raw Snapshot nguyên bản (`crossref_records.json`) để tái lập trình luồng Clean và Re-index Vector DB.

### Nếu có thêm thời gian

Nếu có thêm thời gian, em sẽ triển khai thêm hệ thống **Cảnh báo real-time qua Webhook (Slack/Telegram)** khi Quality Check bị `FAIL`, đồng thời bổ sung thuật toán phát hiện **Data Drift** (sự trôi dạt phân phối vector embedding) theo thời gian.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Hồng Yến  
**Ngày xác nhận:** 2026-08-06
