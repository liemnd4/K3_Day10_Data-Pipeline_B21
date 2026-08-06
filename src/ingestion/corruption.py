from __future__ import annotations

import pandas as pd


import json
import logging
from pathlib import Path
import pandas as pd

from core.utils import normalize_whitespace

logger = logging.getLogger(__name__)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate data corruption on clean dataframe."""
    corrupted_df = df.copy()
    
    log_data = {
        "dropped_latest_records": 0,
        "blank_summaries": 0,
        "injected_noise": 0,
        "truncated_titles": 0,
        "stale_dates": 0,
        "duplicate_rows": 0,
        "total_affected_rows": 0,
    }
    
    n = len(corrupted_df)
    if n < 5:
        logger.warning("Dataframe is too small to perform full corruption.")
        # Minimal logging and output
        with open(output_log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2)
        return corrupted_df

    # 1. Drop some latest records (e.g. drop first 3 rows)
    corrupted_df = corrupted_df.iloc[3:].reset_index(drop=True)
    log_data["dropped_latest_records"] = 3
    
    n = len(corrupted_df)
    
    # Helper to get safe indices
    blank_idx = [0, 1] if n > 1 else ([0] if n > 0 else [])
    noise_idx = [2, 3] if n > 3 else ([2] if n > 2 else [])
    trunc_idx = [4, 5] if n > 5 else ([4] if n > 4 else [])
    stale_idx = [6, 7] if n > 7 else ([6] if n > 6 else [])
    dup_idx = [8, 9] if n > 9 else ([8] if n > 8 else [])

    # 2. Blank summary at some rows
    if blank_idx:
        corrupted_df.loc[blank_idx, "summary"] = ""
        log_data["blank_summaries"] = len(blank_idx)
    
    # 3. Inject noise into summary
    if noise_idx:
        corrupted_df.loc[noise_idx, "summary"] = corrupted_df.loc[noise_idx, "summary"].apply(
            lambda s: str(s) + " [CORRUPT_NOISE_ERROR] gibberish noise injection content."
        )
        log_data["injected_noise"] = len(noise_idx)
    
    # 4. Truncate titles
    if trunc_idx:
        corrupted_df.loc[trunc_idx, "title"] = corrupted_df.loc[trunc_idx, "title"].apply(
            lambda t: str(t)[:5] if t else ""
        )
        log_data["truncated_titles"] = len(trunc_idx)
    
    # 5. Make published date old (stale)
    if stale_idx:
        corrupted_df.loc[stale_idx, "published"] = "1990-01-01"
        corrupted_df.loc[stale_idx, "age_days"] = 10000
        log_data["stale_dates"] = len(stale_idx)
    
    # 6. Add duplicate rows
    if dup_idx:
        dup_rows = corrupted_df.iloc[dup_idx].copy()
        corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
        log_data["duplicate_rows"] = len(dup_idx)
    
    # 7. Rebuild text_for_embedding and summary_chars
    text_for_embedding_list = []
    for _, row in corrupted_df.iterrows():
        title = str(row["title"])
        summary = str(row["summary"])
        categories_joined = str(row["categories_joined"])
        categories = [c.strip() for c in categories_joined.split(",") if c.strip()]
        parts = [title, summary] + categories
        text_for_embedding_list.append(normalize_whitespace(" ".join(parts)))
        
    corrupted_df["text_for_embedding"] = text_for_embedding_list
    corrupted_df["summary_chars"] = corrupted_df["summary"].fillna("").str.len()
    
    log_data["total_affected_rows"] = (
        log_data["dropped_latest_records"]
        + log_data["blank_summaries"]
        + log_data["injected_noise"]
        + log_data["truncated_titles"]
        + log_data["stale_dates"]
        + log_data["duplicate_rows"]
    )
    
    # 8. Write corruption log
    output_log_path = Path(output_log_path)
    output_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Saved corruption log to {output_log_path}")
    return corrupted_df

