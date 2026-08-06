# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Lê Trần Long               |
| MSSV               | 2A202601257                |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | Group B21                  |
| Vai trò chính    | Pipeline Integration & Evidence Owner (Người 5) |
| Repository         | https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21 |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Corruption Simulation | `src/ingestion/corruption.py`<br>- `corrupt_clean_dataframe` | Clean DataFrame (Contract B) | `data/clean/papers_clean_corrupted.csv`<br>`data/results/corruption_log.json` | Hoàn thành |
| Baseline Orchestration | `src/pipelines/phase1.py` | Settings & raw records | `data/results/baseline_metrics.json`<br>`data/reports/phase1_report.md` | Hoàn thành |
| Corruption & Repair Flow | `src/pipelines/corruption_flow.py` | Baseline clean DataFrame & metrics | `data/results/corrupted_metrics.json`<br>`data/results/repaired_metrics.json`<br>`data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Sửa lỗi đọc file CSV trong RAG Index | Người 2 (Cleaning) & Hệ thống RAG | Sửa lỗi `KeyError: 'categories_joined'` bằng cách gọi `.fillna("")` cho DataFrame trước khi gửi sang ChromaDB trong `src/retrieval/index.py`, giải quyết triệt để lỗi NaN khi load dữ liệu. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Mô phỏng lỗi dữ liệu | `src/ingestion/corruption.py`<br>`data/results/corruption_log.json` | Thực hiện chính xác 6 loại lỗi dữ liệu thô (drop, blank, noise, truncate, stale date, duplicate). | Kiểm tra file `corruption_log.json` thấy ghi nhận 13 dòng bị ảnh hưởng. |
| Chạy tích hợp Baseline Pipeline | `src/pipelines/phase1.py`<br>`data/results/baseline_metrics.json` | Chạy end-to-end luồng clean $\rightarrow$ index $\rightarrow$ evaluate thành công. | `uv run python script/run_phase1.py` chạy mượt mà không lỗi. |
| Chạy tích hợp Corruption Flow | `src/pipelines/corruption_flow.py`<br>`data/reports/corruption_report.md` | Đo lường tác động sụt giảm chất lượng của dữ liệu lỗi và kiểm chứng sự phục hồi của dữ liệu repair. | `uv run python script/run_corruption_flow.py` hoàn thành với exit code 0. |

**Mô tả Output cụ thể tạo ra:**
- File báo cáo [`data/reports/corruption_report.md`](file:///d:/AI_ThucChien_Lab/Lab10/data/reports/corruption_report.md) thể hiện đầy đủ, trực quan so sánh 3 trạng thái dữ liệu (Baseline vs Corrupted vs Repaired).
- Các file chỉ số đo lường hiệu năng của mô hình: `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` được ghi nhận đầy đủ, chính xác.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1.  **Mô phỏng lỗi dữ liệu (Data Corruption):** Tạo ra các biến dạng dữ liệu sát với thực tế nhất (mất thông tin tóm tắt, lỗi chính tả/bơm rác, bài báo bị lỗi thời ngày đăng, trùng lặp bản ghi, mất tài liệu mới nhất).
2.  **Đánh giá sự suy giảm hiệu năng (Impact Evaluation):** Đo đạc tác động của dữ liệu lỗi lên chất lượng tìm kiếm ngữ cảnh (Retrieval Hit Rate) và độ tin cậy của câu trả lời từ Agent (Token F1, LLM Judge Score).
3.  **Quy trình khôi phục hoàn toàn tự động (Automated Repair):** Khôi phục dữ liệu từ nguồn thô đáng tin cậy để chứng minh hiệu năng hệ thống RAG có thể quay lại bình thường.

### Cách triển khai
-   **Luồng Corruption:** Copy clean DataFrame ban đầu. Drop 3 dòng đầu tiên. Đặt `summary` rỗng cho index `0, 1`. Bơm văn bản lỗi vào `summary` cho index `2, 3`. Cắt ngắn `title` còn 5 ký tự cho index `4, 5`. Thay đổi `published = "1990-01-01"` và `age_days = 10000` cho index `6, 7`. Sao chép index `8, 9` rồi gộp lại làm trùng lặp. Rebuild lại cột `text_for_embedding` bằng cách ghép Title + Summary + Categories.
-   **Luồng Repair:** Đọc lại raw snapshot từ `crossref_records.json` bằng hàm của Người 1, chuyển qua hàm `build_clean_dataframe` của Người 2 để tạo DataFrame sạch chuẩn, rebuild lại index Chroma riêng (`papers-repaired`) và đánh giá lại.

### Input, output và contract

| Thành phần | Mô tả |
| ------------------------------ | ------------------------------------------- |
| **Input** | `df_clean` (Contract B), `baseline_metrics` (Contract D), `test_set.json` (Contract C). |
| **Output** | Dữ liệu lỗi (`papers_clean_corrupted.csv`), log lỗi (`corruption_log.json`), báo cáo so sánh cuối cùng (`corruption_report.md`). |
| **Module phụ thuộc** | `src/core/config.py`, `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/evaluation/metrics.py`, `src/observability/quality.py`. |
| **Module sử dụng output** | `src/observability/reporting.py` (gọi hàm xuất Markdown report), hệ thống RAG Agent. |

### Cách xác minh

```bash
uv run python script/run_corruption_flow.py
```
-   **Kết quả mong đợi:** Script chạy thành công, tạo đủ các file artifacts, so sánh chỉ số cho thấy chất lượng RAG giảm khi bị lỗi và phục hồi sau khi repair.
-   **Kết quả thực tế:** Hit Rate giảm từ `1.0000` xuống `0.8000`, Token F1 giảm từ `0.9000` xuống `0.6565`. Sau khi repair, Hit Rate tăng lại `1.0000` và Token F1 tăng lại `0.9000`.

---

## 5. Một quyết định kỹ thuật quan trọng

-   **Bối cảnh:** Lựa chọn cách thức lưu trữ và cô lập các index (Chroma collections) giữa các trạng thái Baseline, Corrupted và Repaired.
-   **Các phương án đã cân nhắc:**
    *   *Phương án 1:* Dùng chung một Chroma collection và xóa đi ghi đè lại dữ liệu mỗi khi chạy luồng mới.
    *   *Phương án 2 (Được chọn):* Tạo ra 3 collection riêng biệt (`papers-baseline`, `papers-corrupted`, `papers-repaired`) lưu trong cùng một thư mục `data/chroma`.
-   **Lý do:**
    1.  *Tính cô lập (Isolation):* Đảm bảo dữ liệu ở các pha không bị lẫn lộn hoặc mutate ngầm, giúp phép so sánh hoàn toàn công bằng.
    2.  *Tính audit và khả năng debug:* Nếu kết quả ở trạng thái Corrupted bị lỗi, ta có thể kết nối trực tiếp vào collection `papers-corrupted` để phân tích các vector và khoảng cách tìm kiếm mà không sợ bị ghi đè dữ liệu.
-   **Bằng chứng:** Trong file [`src/retrieval/index.py`](file:///d:/AI_ThucChien_Lab/Lab10/src/retrieval/index.py), hàm `_derive_collection_name` ánh xạ chính xác đường dẫn file lưu manifest sang đúng tên collection.

---

## 6. Một lỗi hoặc blocker đã xử lý

-   **Triệu chứng/lỗi nguyên văn:**
    ```text
    KeyError: 'categories_joined'
    ```
    xảy ra khi chạy luồng đánh giá `evaluate_pipeline` trên tập dữ liệu corrupted.
-   **Lệnh hoặc bước tái hiện:**
    Chạy lệnh `uv run python script/run_corruption_flow.py` trên dữ liệu sau khi được load lại từ file `papers_clean_corrupted.csv`.
-   **Nguyên nhân gốc:**
    Hàm `pd.read_csv(settings.paths.clean_csv)` mặc định chuyển các ô trống hoặc chuỗi rỗng `""` trong file CSV (như `categories_joined` hoặc `authors_joined` bị rỗng ở một số bài báo) thành giá trị float `NaN`. Khi gửi dữ liệu sang ChromaDB làm metadata, Chroma tự động loại bỏ các key chứa giá trị `NaN` (vì Chroma không nhận kiểu float `NaN` cho metadata). Khi RAG thực hiện tìm kiếm và truy xuất thông tin, hàm `_extract_answer` truy cập `metadata["categories_joined"]` và bị crash do key này đã bị Chroma xóa bỏ.
-   **Cách xử lý:**
    1.  Chèn lệnh `df = df.fillna("")` ngay đầu hàm `_build_documents` trong [`src/retrieval/index.py`](file:///d:/AI_ThucChien_Lab/Lab10/src/retrieval/index.py) để đưa mọi giá trị rỗng/NaN về chuỗi trống hợp lệ trước khi gửi sang ChromaDB.
    2.  Dùng tham số `keep_default_na=False` khi load CSV trong [`corruption_flow.py`](file:///d:/AI_ThucChien_Lab/Lab10/src/pipelines/corruption_flow.py).
-   **Cách xác minh sau khi sửa:**
    Chạy lại `run_corruption_flow.py` thành công mượt mà, không gặp lỗi `KeyError` và tạo ra báo cáo so sánh đầy đủ.

---

## 7. Hiểu biết về luồng end-to-end
*(Xem chi tiết trong mục 7 của báo cáo nhóm [`group_report.md`](group_report.md))*

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.8000 |   1.0000 | Retrieval giảm 20% do drop mất bài báo chứa câu trả lời. |
| `mean_token_f1`      |   0.9000 |    0.6565 |   0.9000 | Token F1 sụt giảm mạnh khi Agent phải trả lời bằng summary trống hoặc nhiễu. |
| `judge_accuracy`     |   0.8667 |    0.6167 |   0.8667 | Đánh giá chính xác từ LLM Judge giảm khi Agent bị nhiễu. |
| `mean_judge_score`   |   4.4667 |    3.6000 |   4.4833 | Điểm đánh giá giảm từ 4.47 xuống 3.60, hồi phục hoàn toàn sau repair. |
| Quality checks         |     Pass |      Fail |     Pass | Corrupted báo lỗi trùng lặp và summary ngắn. |
| Freshness status       |    Fresh |     Stale |    Fresh | Corrupted báo stale do bị đổi ngày xuất bản về 1990. |

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1.  **Tầm quan trọng của Data Contract:** Việc quy định chặt chẽ các kiểu dữ liệu và giá trị biên giữa các bước (Ingestion $\rightarrow$ Cleaning $\rightarrow$ Indexing) giúp cả team 5 người làm việc song song hiệu quả mà không bị lỗi giao tiếp dữ liệu.
2.  **Thiết kế Observability từ sớm:** Việc thiết kế các quality checks và freshness monitoring giúp phát hiện các lỗi dữ liệu ngầm trước khi để Agent đưa câu trả lời sai lệch ra cho người dùng.
3.  **Tầm quan trọng của nguồn thô:** Việc lưu trữ cache dữ liệu thô nguyên bản (`data/raw/`) là tối quan trọng để hệ thống có thể khôi phục tự động (Repair) tức thì khi gặp sự cố mà không phụ thuộc vào kết nối API bên ngoài.

### Nếu có thêm thời gian
Em sẽ viết thêm các unit tests tự động (dùng `pytest`) cho từng khâu kiểm tra data quality, đồng thời xây dựng một CLI interface hoàn chỉnh để người dùng có thể chạy và theo dõi luồng baseline/corruption trực quan hơn.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Trần Long  
**Ngày xác nhận:** 2026-08-06
