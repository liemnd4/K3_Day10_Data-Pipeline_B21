from __future__ import annotations


from datetime import datetime, UTC
import logging
from pathlib import Path
import pandas as pd

from core.config import load_settings
from core.utils import read_json
from ingestion.corruption import corrupt_clean_dataframe
from retrieval.index import LocalEmbeddingIndex
from evaluation.metrics import evaluate_pipeline
from observability.quality import run_data_quality_checks, build_freshness_report
from ingestion.crossref import load_raw_records
from ingestion.cleaning import build_clean_dataframe
from observability.reporting import generate_corruption_report

logger = logging.getLogger(__name__)


def main() -> None:
    """Xây dựng corruption -> evaluate -> repair -> compare flow."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logger.info("Initializing corruption & repair flow...")
    settings = load_settings()
    
    # 1. Load baseline metrics và clean dataset
    if not settings.paths.clean_csv.exists() or not settings.paths.baseline_metrics.exists():
        raise RuntimeError(
            "Baseline artifacts missing. Please run the baseline phase1 pipeline first."
        )
        
    logger.info("Loading baseline clean dataset and metrics...")
    df_clean = pd.read_csv(settings.paths.clean_csv, keep_default_na=False)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    
    # 2. Tạo corrupted dataframe
    logger.info("Applying corruption scenario on baseline clean data...")
    df_corrupted = corrupt_clean_dataframe(df_clean, settings.paths.corruption_log)
    
    # 3. Save corrupted artifacts
    corrupted_csv = settings.paths.corrupted_clean_csv
    corrupted_json = settings.paths.corrupted_clean_json
    corrupted_csv.parent.mkdir(parents=True, exist_ok=True)
    df_corrupted.to_csv(corrupted_csv, index=False, encoding="utf-8")
    df_corrupted.to_json(corrupted_json, orient="records", indent=2, force_ascii=False)
    logger.info(f"Saved corrupted data to {corrupted_csv} and {corrupted_json}")

    # 4. Rebuild index và evaluate trên dữ liệu lỗi
    logger.info("Building corrupted Chroma index...")
    index_corrupted = LocalEmbeddingIndex.build(
        df=df_corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json
    )
    
    logger.info("Evaluating corrupted pipeline performance...")
    eval_bundle_corrupted = evaluate_pipeline(
        settings=settings,
        index=index_corrupted,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers
    )
    logger.info(f"Corrupted performance: {eval_bundle_corrupted.summary}")

    # 5. Run quality checks & freshness trên corrupted data
    logger.info("Running corrupted data quality checks...")
    quality_corrupted = run_data_quality_checks(df_corrupted, settings, report_name="corrupted")
    
    logger.info("Running corrupted freshness checks...")
    fresh_report_corrupted_path = settings.paths.quality_dir / "freshness_report_corrupted.json"
    freshness_corrupted = build_freshness_report(df_corrupted, settings, fresh_report_corrupted_path)

    # 6. Repair lại từ raw records
    logger.info("Repairing data: reloading raw records and re-cleaning...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    run_date = datetime.now(UTC)
    df_repaired = build_clean_dataframe(raw_records, run_date)
    
    # Save repaired artifacts
    repaired_csv = settings.paths.repaired_clean_csv
    repaired_json = settings.paths.repaired_clean_json
    repaired_csv.parent.mkdir(parents=True, exist_ok=True)
    df_repaired.to_csv(repaired_csv, index=False, encoding="utf-8")
    df_repaired.to_json(repaired_json, orient="records", indent=2, force_ascii=False)
    logger.info(f"Saved repaired data to {repaired_csv} and {repaired_json}")

    # 7. Evaluate repaired dataset
    logger.info("Building repaired Chroma index...")
    index_repaired = LocalEmbeddingIndex.build(
        df=df_repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json
    )
    
    logger.info("Evaluating repaired pipeline performance...")
    eval_bundle_repaired = evaluate_pipeline(
        settings=settings,
        index=index_repaired,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers
    )
    logger.info(f"Repaired performance: {eval_bundle_repaired.summary}")

    # Run quality checks & freshness trên repaired data
    logger.info("Running repaired data quality checks...")
    quality_repaired = run_data_quality_checks(df_repaired, settings, report_name="repaired")
    
    logger.info("Running repaired freshness checks...")
    fresh_report_repaired_path = settings.paths.quality_dir / "freshness_report_repaired.json"
    freshness_repaired = build_freshness_report(df_repaired, settings, fresh_report_repaired_path)

    # 8. Tạo comparison report
    logger.info("Generating comparison report (corruption & repair comparison)...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=eval_bundle_corrupted.summary,
        repaired_metrics=eval_bundle_repaired.summary,
        corrupted_quality=quality_corrupted,
        repaired_quality=quality_repaired,
        corrupted_freshness=freshness_corrupted,
        repaired_freshness=freshness_repaired,
    )
    logger.info(f"Comparison report successfully written to {settings.paths.comparison_report}")

