# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Văn Hưng            |
| MSSV               | 2A202601970                |
| Khóa/Lớp         | K3                         |
| Tên nhóm         | Group B21                  |
| Vai trò chính    | Evaluation Owner (Người 3 — Evaluation) |
| Repository         | https://github.com/liemnd4/K3_Day10_Data-Pipeline_B21 |
| Ngày hoàn thành | 2026-08-06                 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Test Set Generation & Modeling | `src/evaluation/testset.py`<br>- `build_test_set` | Clean DataFrame (Contract B) từ Người 2 | List `dict` đúng Contract C & `data/eval/test_set.json` | Hoàn thành |
| Multi-aspect Question Synthesis | `src/evaluation/testset.py` | Thông tin `title`, `summary`, `authors_joined`, `published`, `categories_joined` | Bộ 60 câu hỏi đa dạng phủ 4 loại: `summary`, `authors`, `date`, `categories` | Hoàn thành |
| Evaluation Guardrails & Validation | `src/evaluation/testset.py` | Clean DataFrame | Validation `len(df) >= 4`, mapping chuẩn xác `ground_truth_doc_ids` với `paper_id` có thật | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Tối ưu hóa chuỗi truy vấn RAG | Hệ thống RAG (`qa.py` & `agent.py`) | Định dạng tên bài báo trong dấu ngoặc đơn `'...'` trong câu hỏi, giúp QA system đạt hiệu quả kết hợp tối ưu giữa Exact Lookup và Semantic Search. |
| Kiểm thử tự động độc lập | Người 5 (Integration) | Tạo script unit test độc lập kiểm định 100% thuộc tính của đối tượng câu hỏi trước khi đưa vào chạy toàn bộ pipeline. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Sinh bộ Evaluation Test Set | `src/evaluation/testset.py`<br>`build_test_set` | Sinh tự động 60 câu hỏi kiểm thử từ 15 bài báo sạch. | Đọc file `data/eval/test_set.json` kiểm tra đủ 60 phần tử. |
| Kiểm tra Ground Truth Mapping | `data/eval/test_set.json` | 100% `ground_truth_doc_ids` trace chính xác về `paper_id` trong Clean Data. | Assert `item['ground_truth_doc_ids'][0] in set(df['paper_id'])`. |
| Đảm bảo phủ đủ 4 dạng câu hỏi | `data/eval/test_set.json` | Mỗi bài báo sinh đủ 4 loại: `summary` (15), `authors` (15), `date` (15), `categories` (15). | Kiểm tra `set(item['question_type'] for item in test_set) == {'summary', 'authors', 'date', 'categories'}`. |
| Tích hợp luồng đánh giá RAG | `src/evaluation/metrics.py`<br>`evaluate_pipeline` | Cung cấp đầu vào cho `evaluate_pipeline` tính toán các chỉ số `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`. | Chạy thành công qua cả 3 pha Baseline, Corrupted và Repaired. |

**Mô tả Output cụ thể tạo ra:**
- File [`data/eval/test_set.json`](file:///c:/Users/Dell/Downloads/APPLY/VinUni_AI/CODELAB/K3_Day10_Data-Pipeline_B21/data/eval/test_set.json) chứa 60 sample câu hỏi đánh giá chất lượng RAG end-to-end cho cả 3 trạng thái dữ liệu (Baseline, Corrupted, Repaired).

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng module Evaluation Test Set Builder tự động tổng hợp bộ câu hỏi kiểm thử từ Clean DataFrame (`papers_clean.csv` / `.json`), đảm bảo:
1. **Đa dạng hóa loại câu hỏi:** Phụ trách đánh giá nhiều khía cạnh khác nhau của hệ thống RAG (Tóm tắt nội dung, Tra cứu tác giả, Ngày xuất bản, Phân loại chủ đề).
2. **Truy xuất nguồn gốc 100% (Traceability):** Mọi câu hỏi phải được liên kết chính xác với `paper_id` thực sự tồn tại trong tập dữ liệu (`ground_truth_doc_ids`).
3. **Độ chính xác của Ground Truth:** Chiết xuất đáp án chuẩn xác từ dữ liệu thô đã làm sạch (`authors_joined`, `published`, `categories_joined`, `first_sentence(summary)`) để làm căn cứ chấm điểm cho LLM Judge và Token F1.
4. **Cung cấp thước đo cho Data Observability:** Làm cơ sở định lượng sự sụt giảm hiệu năng khi dữ liệu bị tiêm lỗi (Corrupted) và khôi phục khi phục hồi dữ liệu (Repaired).

### Cách triển khai

1. **Validation & Kiểm tra điều kiện đầu vào:**
   - Kiểm tra xem DataFrame đầu vào có rỗng hoặc nhỏ hơn 4 tài liệu hay không:
     ```python
     if df.empty or len(df) < 4:
         raise ValueError(f"Cleaned dataframe must contain at least 4 documents to build a valid test set, got {len(df)}.")
     ```
2. **Lấy mẫu đại diện:** Chọn 15 bài báo tiêu biểu từ `df.head(15)` để tạo bộ câu hỏi có tính đại diện cao.
3. **Tạo 4 loại câu hỏi theo template chuẩn:**
   - **Summary:** `"What is the summary of the paper '{title}'?"` $\rightarrow$ Ground truth: `first_sentence(summary)` (hoặc `title` nếu summary rỗng).
   - **Authors:** `"Who authored the paper '{title}'?"` $\rightarrow$ Ground truth: `authors_joined`.
   - **Date:** `"When was the paper '{title}' published?"` $\rightarrow$ Ground truth: `published`.
   - **Categories:** `"What categories does the paper '{title}' belong to?"` $\rightarrow$ Ground truth: `categories_joined`.
4. **Bao đóng đối tượng theo Contract C:**
   ```python
   {
       "id": f"q_{index:03d}_{q_type}",
       "question_type": q_type,
       "question": question_text,
       "ground_truth": ground_truth_text,
       "ground_truth_doc_ids": [paper_id],
   }
   ```
5. **Ghi file an toàn:** Sử dụng hàm utility `write_json` từ `core.utils` đảm bảo thư mục đích `data/eval/` được tạo tự động nếu chưa tồn tại.

---

## 5. Đóng góp vào kết quả chung của nhóm

Bộ dữ liệu đánh giá `test_set.json` do Người 3 xây dựng đóng vai trò là thước đo trung tâm (Benchmarking) cho toàn bộ dự án của nhóm B21. Kết quả từ bộ test set đã chứng minh bằng số liệu thực tế tác động trực tiếp của Data Quality tới RAG Agent:

| Trạng thái Dữ liệu | Retrieval Hit Rate | Mean Token F1 | LLM Judge Accuracy | Mean Judge Score |
| ------------------- | ------------------ | ------------- | ------------------ | ---------------- |
| **Baseline (Clean)** | **1.0000 (100%)** | **0.9000** | **1.0000 (100%)** | **5.00** |
| **Corrupted (Hỏng)** | **0.8000 (80%)** | **0.6565** | **0.6500 (65%)** | **3.60** |
| **Repaired (Sửa)** | **1.0000 (100%)** | **0.9000** | **1.0000 (100%)** | **5.00** |

- **Phân tích tác động:** Khi dữ liệu bị làm hỏng (xóa bài báo mới, rỗng summary, nhiễu text, lùi ngày xuất bản), Hit Rate giảm 20%, Token F1 giảm 27% và Judge Accuracy giảm tới 35%. Khi thực hiện Repair từ dữ liệu gốc, các chỉ số đã khôi phục hoàn toàn về mức Baseline ban đầu.

---

## 6. Bài học kinh nghiệm và tự đánh giá

- **Bài học kinh nghiệm:**
  - Việc thiết kế câu hỏi trong bộ test set cần phản ánh đúng cách thức tra cứu của bộ phận QA (`qa.py`). Việc bao quanh tiêu đề bằng dấu `'...'` cho phép hệ thống RAG vừa có thể Exact Lookup thành công, vừa kiểm thử được tính năng Semantic Search thông qua vector embedding.
  - Cần kiểm tra kỹ các trường ground truth để tránh tình trạng null hoặc rỗng dẫn đến tính toán chỉ số Token F1 bị sai lệch.
- **Tự đánh giá:** Hoàn thành 100% nhiệm vụ đúng hạn, mã nguồn được thiết kế sạch sẽ, tuần thủ tuyệt đối Contract C và tích hợp mượt mà vào hệ thống chung của nhóm.
