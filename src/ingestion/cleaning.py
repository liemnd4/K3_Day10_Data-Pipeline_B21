from __future__ import annotations

from datetime import datetime
import logging

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord

logger = logging.getLogger(__name__)

MIN_EMBEDDING_TEXT_CHARS = 10

CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors_joined",
    "categories_joined",
    "primary_category",
    "published",
    "updated",
    "age_days",
    "summary_chars",
    "text_for_embedding",
    "abs_url",
    "pdf_url",
    "comment",
]


def _normalize_items(values: list[str]) -> list[str]:
    return [cleaned for value in values if (cleaned := normalize_whitespace(value))]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw paper records into the dataframe defined by Contract B."""
    raw_count = len(records)
    rows: list[dict] = []

    for record in records:
        authors = _normalize_items(record.authors)
        categories = _normalize_items(record.categories)
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        primary_category = normalize_whitespace(record.primary_category)
        text_parts = [title, summary, *categories]

        rows.append(
            {
                "paper_id": normalize_whitespace(record.paper_id),
                "title": title,
                "summary": summary,
                "authors_joined": ", ".join(authors),
                "categories_joined": ", ".join(categories),
                "primary_category": primary_category,
                "published": record.published,
                "updated": record.updated,
                "summary_chars": len(summary),
                "text_for_embedding": normalize_whitespace(" ".join(text_parts)),
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
            }
        )

    if not rows:
        logger.info("Cleaning rows: raw=0 clean=0 removed=0")
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    df = pd.DataFrame(rows)

    missing_id_mask = df["paper_id"].eq("")
    missing_id_count = int(missing_id_mask.sum())
    df = df.loc[~missing_id_mask].copy()

    duplicate_mask = df.duplicated(subset="paper_id", keep="first")
    duplicate_count = int(duplicate_mask.sum())
    df = df.loc[~duplicate_mask].copy()

    published_dates = pd.to_datetime(df["published"], errors="coerce")
    updated_dates = pd.to_datetime(df["updated"], errors="coerce")
    invalid_date_mask = published_dates.isna() | updated_dates.isna()
    invalid_date_count = int(invalid_date_mask.sum())
    df = df.loc[~invalid_date_mask].copy()
    published_dates = published_dates.loc[~invalid_date_mask]
    updated_dates = updated_dates.loc[~invalid_date_mask]

    short_text_mask = df["text_for_embedding"].str.len() < MIN_EMBEDDING_TEXT_CHARS
    short_text_count = int(short_text_mask.sum())
    df = df.loc[~short_text_mask].copy()
    published_dates = published_dates.loc[~short_text_mask]
    updated_dates = updated_dates.loc[~short_text_mask]

    effective_run_date = pd.Timestamp(run_date)
    if effective_run_date.tzinfo is not None:
        effective_run_date = effective_run_date.tz_localize(None)

    df["published"] = published_dates.dt.strftime("%Y-%m-%d")
    df["updated"] = updated_dates.dt.strftime("%Y-%m-%d")
    df["age_days"] = (effective_run_date.normalize() - published_dates.dt.normalize()).dt.days.astype(int)

    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    df = df[CLEAN_COLUMNS]

    clean_count = len(df)
    logger.info(
        "Cleaning rows: raw=%d clean=%d removed=%d "
        "(missing_paper_id=%d, duplicates=%d, invalid_dates=%d, invalid_embedding_text=%d)",
        raw_count,
        clean_count,
        raw_count - clean_count,
        missing_id_count,
        duplicate_count,
        invalid_date_count,
        short_text_count,
    )
    return df
