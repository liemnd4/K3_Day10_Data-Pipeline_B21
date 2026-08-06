from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set từ cleaned dataframe theo đúng Contract C."""
    if df.empty or len(df) < 4:
        raise ValueError(
            f"Cleaned dataframe must contain at least 4 documents to build a valid test set, got {len(df)}."
        )

    test_set: list[dict[str, Any]] = []

    # Chọn tối đa 15 bài báo đại diện từ dataframe
    sample_df = df.head(15)

    for index, (_, row) in enumerate(sample_df.iterrows(), start=1):
        paper_id = str(row["paper_id"])
        title = str(row["title"])
        summary = str(row.get("summary", ""))
        authors_joined = str(row.get("authors_joined", ""))
        published = str(row.get("published", ""))
        categories_joined = str(row.get("categories_joined", ""))

        ground_truth_summary = first_sentence(summary) if summary else title

        # 1. Summary
        test_set.append({
            "id": f"q_{index:03d}_summary",
            "question_type": "summary",
            "question": f"What is the summary of the paper '{title}'?",
            "ground_truth": ground_truth_summary,
            "ground_truth_doc_ids": [paper_id],
        })

        # 2. Authors
        test_set.append({
            "id": f"q_{index:03d}_authors",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": authors_joined,
            "ground_truth_doc_ids": [paper_id],
        })

        # 3. Date
        test_set.append({
            "id": f"q_{index:03d}_date",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": published,
            "ground_truth_doc_ids": [paper_id],
        })

        # 4. Categories
        test_set.append({
            "id": f"q_{index:03d}_categories",
            "question_type": "categories",
            "question": f"What categories does the paper '{title}' belong to?",
            "ground_truth": categories_joined,
            "ground_truth_doc_ids": [paper_id],
        })

    target_path = Path(output_path)
    write_json(target_path, test_set)
    return test_set

