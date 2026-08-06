from __future__ import annotations


from datetime import datetime, UTC
import logging
from pathlib import Path
import pandas as pd

from core.config import load_settings
from ingestion.crossref import fetch_source_records, load_raw_records
from ingestion.cleaning import build_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from observability.reporting import generate_phase1_report
from retrieval.qa import answer_question

logger = logging.getLogger(__name__)


def main() -> None:
    """Xây dựng baseline pipeline end-to-end cho dữ liệu sạch."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logger.info("Initializing phase 1 baseline pipeline...")
    settings = load_settings()
    
    # 1. Ingest raw records
    raw_records_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_records_path.exists():
        logger.info("Fetching raw records from source...")
        records = fetch_source_records(settings)
    else:
        logger.info(f"Loading raw records from cache: {raw_records_path}")
        records = load_raw_records(raw_records_path)

    # 2. Clean data
    run_date = datetime.now(UTC)
    logger.info(f"Cleaning data (run_date: {run_date})...")
    df_clean = build_clean_dataframe(records, run_date)
    
    # 3. Save clean CSV/JSON
    clean_csv = settings.paths.clean_csv
    clean_json = settings.paths.clean_json
    clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(clean_csv, index=False, encoding="utf-8")
    df_clean.to_json(clean_json, orient="records", indent=2, force_ascii=False)
    logger.info(f"Saved cleaned data to {clean_csv} and {clean_json}")

    # 4. Build Chroma index
    logger.info("Building baseline Chroma index...")
    index = LocalEmbeddingIndex.build(
        df=df_clean,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json
    )

    # 5. Create or load evaluation set
    test_set_path = settings.paths.eval_testset
    if settings.refresh_test_set or not test_set_path.exists():
        logger.info("Generating a new test set...")
        build_test_set(df_clean, test_set_path)
    else:
        logger.info(f"Loading existing test set from {test_set_path}")

    # 6. Evaluate baseline
    logger.info("Evaluating baseline pipeline performance...")
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=test_set_path,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers
    )
    logger.info(f"Baseline performance: {eval_bundle.summary}")

    # 7. Run quality checks & freshness report
    logger.info("Running baseline data quality checks...")
    quality_report = run_data_quality_checks(df_clean, settings, report_name="baseline")
    
    logger.info("Running baseline freshness checks...")
    freshness_report = build_freshness_report(df_clean, settings, settings.paths.freshness_report)

    # 8. Generate baseline report (Phase 1)
    logger.info("Generating baseline report...")
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "raw_count": len(records),
        "clean_count": len(df_clean),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_report,
        freshness=freshness_report,
    )
    logger.info(f"Baseline report successfully written to {settings.paths.baseline_report}")

    # 9. Demo agent
    if not df_clean.empty:
        logger.info("--- Sample Agent Demo Query ---")
        first_title = df_clean.iloc[0]["title"]
        q = f"Who authored the paper '{first_title}'?"
        ans_res = answer_question(q, settings, index)
        logger.info(f"Question: {q}")
        logger.info(f"Answer: {ans_res.answer}")

