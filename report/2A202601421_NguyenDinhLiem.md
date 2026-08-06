# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Đình Liêm |
| MSSV | 2A202601421 |
| Khóa/Lớp | K3 |
| Tên nhóm | B21 |
| Vai trò chính | Cleaning & Data Modeling |
| Repository | [liemnd4/K3_Day10_Data-Pipeline_B21](https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21) |
| Ngày hoàn thành | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning & Data Modeling | `src/ingestion/cleaning.py`<br>`build_clean_dataframe` | `list[PaperRecord]` từ Người 1 và `run_date` | Clean `pandas.DataFrame` đúng Contract B | Hoàn thành |
| Chuẩn hóa và tạo trường dẫn xuất | `src/ingestion/cleaning.py` | Các trường text, authors, categories và ngày từ raw record | `authors_joined`, `categories_joined`, `age_days`, `summary_chars`, `text_for_embedding` | Hoàn thành |
| Lọc và kiểm soát dữ liệu xấu | `src/ingestion/cleaning.py` | DataFrame trung gian | DataFrame có `paper_id` unique, ngày hợp lệ, embedding text hợp lệ và log số dòng bị loại | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Xác minh contract đầu ra | Người 3, Người 4 và Người 5 | Kiểm tra đủ 14 cột Contract B, `paper_id` unique và `text_for_embedding` không rỗng. |
| Kiểm tra bằng snapshot raw thật | Người 5 — Integration | Chạy hàm với 24 `PaperRecord`; nhận 24 dòng sạch để pipeline lưu CSV/JSON và dùng ở các bước sau. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Chuẩn hóa dữ liệu text | `build_clean_dataframe` | Loại khoảng trắng thừa trong title, summary, authors, categories và primary category. | So sánh giá trị đầu vào có khoảng trắng với giá trị trong DataFrame. |
| Chuyển đổi schema | `build_clean_dataframe` | Tạo DataFrame đủ 14 cột đúng thứ tự Contract B. | Kiểm tra `df.columns.tolist()`. |
| Tạo dữ liệu phục vụ embedding và observability | `text_for_embedding`, `age_days`, `summary_chars` | Embedding text không rỗng; tuổi tài liệu và độ dài summary được tính tự động. | Assertion trên kiểu dữ liệu và giá trị dẫn xuất. |
| Dedupe và lọc bản ghi xấu | `paper_id`, `published`, `updated`, `text_for_embedding` | Loại ID rỗng/trùng, ngày lỗi và embedding text quá ngắn; log count theo nguyên nhân. | Chạy dữ liệu mẫu chứa từng loại lỗi và đọc log cleaning. |
| Xác minh đầu ra tích hợp | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Artifact hiện có 24 dòng, 14 cột; không có ID null/trùng. | Đối chiếu CSV với `data/quality/baseline_quality.json`. |

**Mô tả output cụ thể tạo ra:**

- Module của em trả về clean DataFrame; Người 5 gọi hàm này trong `phase1.py` và chịu trách nhiệm lưu artifact.
- Artifact tích hợp `data/clean/papers_clean.csv` và `.json` chứa 24 bài báo theo Contract B.
- Báo cáo baseline ghi nhận `paper_id_null_count = 0`, `paper_id_duplicate_count = 0` và `checks_passed = true`.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Dữ liệu do Người 1 bàn giao là `list[PaperRecord]`, vẫn chứa các trường danh sách và chưa có những cột mà embedding, evaluation và observability cần. Nhiệm vụ của em là viết hàm chuyển đổi dữ liệu này thành DataFrame ổn định theo Contract B, đồng thời không làm mất bản ghi âm thầm.

### Cách triển khai

- Dùng `normalize_whitespace` để chuẩn hóa title, summary, từng author, từng category và primary category.
- Ghép authors/categories bằng dấu `, ` để tạo metadata dạng chuỗi.
- Parse `published` và `updated` bằng `pandas.to_datetime`, sau đó xuất lại định dạng ISO `YYYY-MM-DD`.
- Tính `age_days = (run_date - published).days` và `summary_chars = len(summary)`.
- Ghép title, summary và categories thành `text_for_embedding`.
- Loại ID rỗng, dedupe theo `paper_id` và giữ bản ghi đầu tiên.
- Loại dòng có ngày không parse được hoặc embedding text ngắn hơn ngưỡng hợp lệ.
- Log số dòng raw, clean và số bị loại theo từng nguyên nhân; sau đó sort theo ngày xuất bản giảm dần và `paper_id` tăng dần.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| **Input** | `records: list[PaperRecord]`, `run_date: datetime`. |
| **Output** | `pandas.DataFrame` gồm đúng 14 cột Contract B. |
| **Module phụ thuộc** | `ingestion.crossref.PaperRecord`, `core.utils.normalize_whitespace`, pandas. |
| **Module sử dụng output** | Evaluation, Observability và Integration/Pipeline. |
| **Điều kiện lỗi cần xử lý** | ID rỗng/trùng, ngày không hợp lệ, embedding text rỗng hoặc quá ngắn. |

### Cách xác minh

```powershell
$env:PYTHONPATH="src"
uv run python -c "from datetime import datetime; from pathlib import Path; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; records = load_raw_records(Path('data/raw/crossref_records.json')); df = build_clean_dataframe(records, datetime(2026, 8, 6)); print(df.shape); print(df.columns.tolist()); assert df['paper_id'].is_unique; assert df['text_for_embedding'].str.strip().ne('').all()"
```

- **Kết quả mong đợi:** DataFrame đúng 14 cột, ID unique và không có embedding text rỗng.
- **Kết quả thực tế:** `(24, 14)`; 24/24 ID unique và toàn bộ embedding text hợp lệ.
- **Artifact đối chiếu:** `data/clean/papers_clean.csv`, `data/clean/papers_clean.json`, `data/quality/baseline_quality.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn nội dung đưa vào `text_for_embedding` trong giới hạn Contract B.
- **Các phương án đã cân nhắc:**
  - Chỉ dùng title và summary.
  - Dùng title, summary và categories.
- **Phương án đã chọn:** Ghép title, summary và categories đã normalize.
- **Lý do:** Title và summary cung cấp nội dung chính; categories bổ sung tín hiệu chủ đề để hỗ trợ semantic retrieval. Việc ghép chỉ dùng dữ liệu sẵn có, không thay đổi `paper_id` hay thông tin nguồn.
- **Bằng chứng quyết định phù hợp:** Baseline đạt `retrieval_hit_rate = 1.0`; toàn bộ 24 dòng có `text_for_embedding` hợp lệ.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Bài kiểm tra mong bản ghi có title `x` bị loại vì embedding quá ngắn, nhưng DataFrame vẫn giữ bản ghi đó.
- **Bước tái hiện:** Tạo record có title `x`, summary rỗng nhưng vẫn truyền categories `ML`, `Data Science`.
- **Nguyên nhân gốc:** `text_for_embedding` được phép ghép thêm categories, nên chuỗi thực tế là `x ML Data Science` và không còn quá ngắn. Dữ liệu kiểm tra chưa thật sự biểu diễn trường hợp embedding không hợp lệ.
- **Cách xử lý:** Sửa fixture kiểm tra bằng cách để cả summary và categories rỗng; không sửa sai logic production chỉ để làm test pass.
- **Cách xác minh sau khi sửa:** Chạy lại kiểm tra và nhận log `invalid_embedding_text=1`; các dòng hợp lệ vẫn được giữ nguyên.
- **Bài học kỹ thuật:** Khi kiểm thử trường dẫn xuất, cần kiểm tra toàn bộ dữ liệu tham gia tạo trường đó, không chỉ một cột đầu vào.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Người 1 lấy Crossref payload, parse thành `list[PaperRecord]` và lưu raw snapshot. Hàm cleaning của em chuyển list này thành clean DataFrame. Người 5 gọi hàm, lưu CSV/JSON rồi truyền `text_for_embedding` sang `LocalEmbeddingIndex` để tạo vector và nạp ChromaDB.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi câu hỏi có `ground_truth_doc_ids` trỏ tới `paper_id` thật trong clean DataFrame. Kết quả retrieval được tính hit khi top-k chứa ID đúng; câu trả lời được so sánh với ground truth để tính token F1 và judge metrics. Vì vậy cleaning phải giữ `paper_id` ổn định.

3. **Quality checks khác freshness monitoring ở điểm nào?**
   Quality kiểm tra tính toàn vẹn như ID null/trùng, title null và summary ngắn. Freshness dùng `published` và `age_days` để xác định tài liệu có vượt ngưỡng stale hay không.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Giữ cùng câu hỏi và ground truth giúp cô lập tác động của việc làm hỏng và sửa dữ liệu; thay test set sẽ khiến so sánh metrics không công bằng.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Clean repaired phải khôi phục schema, ID và quality/freshness. Trong artifact hiện tại, repaired có 24 dòng, quality pass, freshness true; `retrieval_hit_rate` trở lại `1.0`, bằng baseline.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Corruption làm mất 20% retrieval hit; repair phục hồi hoàn toàn. |
| `mean_token_f1` | 0.9000 | 0.6565 | 0.9000 | Chất lượng câu trả lời giảm khi dữ liệu lỗi và trở lại baseline sau repair. |
| `judge_accuracy` | 0.8667 | 0.6167 | 0.8667 | Dữ liệu sạch giúp độ chính xác đánh giá phục hồi. |
| `mean_judge_score` | 4.4667 | 3.6000 | 4.4833 | Điểm repaired xấp xỉ và nhỉnh hơn nhẹ baseline. |
| Quality checks | Pass | Fail | Pass | Corrupted có 2 ID trùng và 2 summary ngắn; repaired loại bỏ lỗi. |
| Freshness status | Fresh | Stale | Fresh | Corrupted có 2 dòng stale; repaired trở lại 0 dòng stale. |

Các số liệu trên được đọc từ `data/results/*_metrics.json` và `data/quality/*.json`, không hard-code theo kỳ vọng.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Data contract giúp các thành viên phát triển song song; chỉ cần đầu vào và đầu ra đúng schema thì module có thể tích hợp ổn định.
2. **Về Data Quality & Observability:** Mọi thao tác drop/dedupe phải có count và lý do để giải thích chênh lệch raw → clean.
3. **Về ảnh hưởng của Data tới RAG Agent:** Cleaning không chỉ làm dữ liệu đẹp hơn; ID, ngày và embedding text quyết định trực tiếp retrieval, freshness và độ chính xác câu trả lời.

### Nếu có thêm thời gian

Em sẽ bổ sung bộ unit test cố định cho từng quy tắc Contract B, đặc biệt các trường hợp ngày lỗi, dữ liệu Unicode, danh sách authors/categories rỗng và record trùng ID, để phát hiện regression trước khi chạy pipeline end-to-end.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đình Liêm

**Ngày xác nhận:** 2026-08-06
