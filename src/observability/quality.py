from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tạo bộ data quality checks theo Contract D và lưu kết quả JSON vào settings.paths.quality_dir."""
    import json
    from pathlib import Path

    row_count = len(df)
    
    # 1. paper_id null count
    if "paper_id" in df.columns:
        paper_id_null_count = int(df["paper_id"].isna().sum() + (df["paper_id"].astype(str).str.strip() == "").sum())
        paper_id_duplicate_count = int(df["paper_id"].duplicated().sum())
    else:
        paper_id_null_count = row_count
        paper_id_duplicate_count = 0

    # 2. title null count
    if "title" in df.columns:
        title_null_count = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum())
    else:
        title_null_count = row_count

    # 3. summary short count (< 20 characters or missing/empty)
    if "summary" in df.columns:
        summary_series = df["summary"].fillna("").astype(str).str.strip()
        summary_short_count = int((summary_series.str.len() < 20).sum())
    else:
        summary_short_count = row_count

    failures: list[str] = []
    if paper_id_null_count > 0:
        failures.append("paper_id_null_check")
    if paper_id_duplicate_count > 0:
        failures.append("paper_id_duplicate_check")
    if title_null_count > 0:
        failures.append("title_null_check")
    if summary_short_count > 0:
        failures.append("summary_short_check")

    checks_passed = len(failures) == 0

    quality_report = {
        "report_name": report_name,
        "row_count": row_count,
        "paper_id_null_count": paper_id_null_count,
        "paper_id_duplicate_count": paper_id_duplicate_count,
        "title_null_count": title_null_count,
        "summary_short_count": summary_short_count,
        "checks_passed": checks_passed,
        "failures": failures,
    }

    # Save to quality_dir/f"{report_name}_quality.json"
    quality_dir = Path(settings.paths.quality_dir)
    quality_dir.mkdir(parents=True, exist_ok=True)
    out_file = quality_dir / f"{report_name}_quality.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2, ensure_ascii=False)

    return quality_report



def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Tổng hợp freshness report theo Contract D và lưu JSON report."""
    import json
    from pathlib import Path

    total_rows = len(df)

    if total_rows == 0:
        freshness_payload = {
            "latest_published": "",
            "oldest_published": "",
            "stale_rows": 0,
            "total_rows": 0,
            "is_fresh": False,
        }
    else:
        # Find latest and oldest published date
        if "published" in df.columns:
            published_series = pd.to_datetime(df["published"], errors="coerce").dropna()
            if not published_series.empty:
                latest_published = str(published_series.max().strftime("%Y-%m-%d"))
                oldest_published = str(published_series.min().strftime("%Y-%m-%d"))
            else:
                latest_published = ""
                oldest_published = ""
        else:
            latest_published = ""
            oldest_published = ""

        # Count stale rows (age_days > freshness_threshold_days)
        threshold = settings.freshness_threshold_days
        if "age_days" in df.columns:
            stale_rows = int((df["age_days"] > threshold).sum())
        elif "published" in df.columns and latest_published:
            run_date = pd.to_datetime("now", utc=True).tz_localize(None)
            pub_dates = pd.to_datetime(df["published"], errors="coerce").dt.tz_localize(None)
            calculated_age = (run_date - pub_dates).dt.days
            stale_rows = int((calculated_age > threshold).sum())
        else:
            stale_rows = total_rows

        is_fresh = (stale_rows == 0) and (total_rows > 0)

        freshness_payload = {
            "latest_published": latest_published,
            "oldest_published": oldest_published,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "is_fresh": is_fresh,
        }

    # Write JSON report
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(freshness_payload, f, indent=2, ensure_ascii=False)

    return freshness_payload

