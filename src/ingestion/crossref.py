from __future__ import annotations

from dataclasses import asdict, dataclass
import html
import json
import logging
from pathlib import Path
import re
import time
from typing import Any

import requests

from core.config import Settings

logger = logging.getLogger(__name__)

CROSSREF_API_URL = "https://api.crossref.org/works"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(text: str | None) -> str:
    """Loại bỏ XML/HTML tags và normalize whitespace."""
    if not text:
        return ""
    # Strip HTML/XML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities e.g. &amp;, &lt;
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    return " ".join(cleaned.split())


def _parse_date_parts(date_struct: dict[str, Any] | None) -> str:
    """Rút gọn `date-parts` từ Crossref payload thành chuỗi ISO 'YYYY-MM-DD'."""
    if not date_struct or not isinstance(date_struct, dict):
        return ""
    date_parts = date_struct.get("date-parts")
    if not date_parts or not isinstance(date_parts, list) or not date_parts[0]:
        return ""

    parts = date_parts[0]
    year = int(parts[0]) if len(parts) > 0 and parts[0] is not None else 1970
    month = int(parts[1]) if len(parts) > 1 and parts[1] is not None else 1
    day = int(parts[2]) if len(parts) > 2 and parts[2] is not None else 1

    return f"{year:04d}-{month:02d}-{day:02d}"


def _extract_dates(item: dict[str, Any]) -> tuple[str, str]:
    """Lấy published date và updated date từ Crossref item."""
    published = (
        _parse_date_parts(item.get("published-online"))
        or _parse_date_parts(item.get("published-print"))
        or _parse_date_parts(item.get("issued"))
        or _parse_date_parts(item.get("created"))
    )

    updated = (
        _parse_date_parts(item.get("deposited"))
        or _parse_date_parts(item.get("indexed"))
    )

    if not published:
        published = "1970-01-01"
    if not updated:
        updated = published

    return published, updated


def _extract_authors(item: dict[str, Any]) -> list[str]:
    """Lấy danh sách tên tác giả."""
    authors: list[str] = []
    author_list = item.get("author", [])
    if not isinstance(author_list, list):
        return authors

    for a in author_list:
        if not isinstance(a, dict):
            continue
        given = str(a.get("given", "")).strip()
        family = str(a.get("family", "")).strip()
        name = f"{given} {family}".strip() if (given or family) else str(a.get("name", "")).strip()
        if name:
            authors.append(name)
    return authors


def _extract_pdf_url(item: dict[str, Any]) -> str:
    """Lấy URL file PDF nếu có trong trường link."""
    links = item.get("link", [])
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict) and link.get("content-type") == "application/pdf":
                url = link.get("URL", "").strip()
                if url:
                    return url
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thành danh sách PaperRecord tuân thủ Contract A.

    1. Duyệt `payload["message"]["items"]`.
    2. Lấy DOI (làm stable paper_id), title, abstract, authors, categories, dates, URLs.
    3. Loại bỏ record thiếu DOI hoặc thiếu title.
    4. Trả về danh sách `PaperRecord`.
    """
    message = payload.get("message", {}) if isinstance(payload, dict) else {}
    items = message.get("items", []) if isinstance(message, dict) else []

    records: list[PaperRecord] = []
    seen_paper_ids: set[str] = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        raw_doi = item.get("DOI", "")
        if not raw_doi or not isinstance(raw_doi, str):
            continue

        # Chuẩn hóa DOI thành stable paper_id
        doi = raw_doi.strip()
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]
        elif doi.startswith("http://dx.doi.org/"):
            doi = doi[len("http://dx.doi.org/"):]
        paper_id = doi.strip()

        if not paper_id or paper_id in seen_paper_ids:
            continue

        # Lấy title
        raw_titles = item.get("title", [])
        if isinstance(raw_titles, list) and raw_titles:
            raw_title = str(raw_titles[0])
        elif isinstance(raw_titles, str):
            raw_title = raw_titles
        else:
            raw_title = ""

        title = _clean_text(raw_title)
        if not title:  # Yêu cầu Contract A: Bỏ qua nếu thiếu title
            continue

        # Abstract / summary
        summary = _clean_text(item.get("abstract", ""))

        # Authors
        authors = _extract_authors(item)

        # Categories
        subjects = item.get("subject", [])
        if isinstance(subjects, list):
            categories = [_clean_text(str(s)) for s in subjects if str(s).strip()]
        else:
            categories = []

        if not categories:
            container = item.get("container-title", [])
            if isinstance(container, list):
                categories = [_clean_text(str(c)) for c in container if str(c).strip()]

        primary_category = categories[0] if categories else ""

        # Dates
        published, updated = _extract_dates(item)

        # URLs
        abs_url = str(item.get("URL", "")).strip() or f"https://doi.org/{paper_id}"
        pdf_url = _extract_pdf_url(item)

        # Comment / type / publisher info
        comment = str(item.get("publisher", "")).strip()

        record = PaperRecord(
            paper_id=paper_id,
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=primary_category,
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment=comment,
        )

        records.append(record)
        seen_paper_ids.add(paper_id)

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi source API (Crossref), lưu raw response, parse thành records và lưu raw records snapshot."""
    params: dict[str, Any] = {
        "query": settings.source_query,
        "rows": settings.max_results,
    }
    if settings.source_filter:
        params["filter"] = settings.source_filter

    headers = {
        "User-Agent": "DataPipelineLab/1.0 (mailto:student@vinai.io)"
    }

    max_retries = 5
    backoff_factor = 1.0
    payload: dict[str, Any] | None = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Calling Crossref API (attempt {attempt}/{max_retries})...")
            response = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=30)

            if response.status_code in (429, 503):
                wait_time = backoff_factor * (2 ** (attempt - 1))
                logger.warning(f"Got HTTP {response.status_code}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            payload = response.json()
            break
        except requests.RequestException as e:
            if attempt == max_retries:
                logger.error(f"Failed to fetch from Crossref API after {max_retries} attempts: {e}")
                raise
            wait_time = backoff_factor * (2 ** (attempt - 1))
            logger.warning(f"Request error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    if payload is None:
        raise RuntimeError("Failed to obtain payload from Crossref API.")

    # 1. Lưu raw API response gốc trước khi parse
    raw_api_path = settings.paths.raw_api_response
    raw_api_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_api_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved raw API response to {raw_api_path}")

    # 2. Parse payload thành list PaperRecord
    records = parse_crossref_payload(payload)

    # 3. Lưu parsed raw records snapshot
    raw_records_path = settings.paths.raw_records_json
    raw_records_path.parent.mkdir(parents=True, exist_ok=True)
    records_dict_list = [asdict(r) for r in records]
    with open(raw_records_path, "w", encoding="utf-8") as f:
        json.dump(records_dict_list, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(records)} parsed raw records to {raw_records_path}")

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành list `PaperRecord`."""
    if not path.exists():
        raise FileNotFoundError(f"Raw records file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data_list = json.load(f)

    if not isinstance(data_list, list):
        raise ValueError(f"Expected a JSON list in {path}, got {type(data_list)}")

    records: list[PaperRecord] = []
    for item in data_list:
        if isinstance(item, dict):
            records.append(PaperRecord(**item))
    return records

