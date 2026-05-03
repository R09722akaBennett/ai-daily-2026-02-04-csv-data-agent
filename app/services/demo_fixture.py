"""Pre-baked extraction so prospects can demo the UI without installing 5GB of models.

The fixture is a realistic-shaped ``ExtractedDocument`` covering the four
features that matter at sales time: tables, headings, page citations, and
quality warnings. Treat this as marketing copy that compiles.
"""

from __future__ import annotations

from app.core.types import ExtractedDocument, ExtractedSection, ExtractedTable, QualitySignal

_MARKDOWN = """# 2025 Annual Vendor Compliance Report

## 1. Executive Summary

This report summarizes the compliance status of our 38 active SaaS vendors
across PDPA, GDPR, and SOC 2 dimensions for fiscal year 2025. 4 vendors require
remediation before Q1 2026 contract renewal.

## 2. Findings by Region

### 2.1 APAC

All 14 APAC vendors are compliant with PDPA Taiwan and Singapore PDPA. Two
vendors (Vendor A, Vendor B) have outstanding sub-processor disclosures.

### 2.2 EU

12 of 13 EU vendors are GDPR-compliant. Vendor C lacks a Standard Contractual
Clause for cross-border transfers and must be remediated by 2026-01-15.

## 3. Risk Matrix

See Table 1 for the breakdown by severity.
"""


def build_demo_document() -> ExtractedDocument:
    sections = [
        ExtractedSection(
            heading="Executive Summary",
            level=2,
            heading_path=["2025 Annual Vendor Compliance Report", "Executive Summary"],
            text=(
                "This report summarizes the compliance status of our 38 active SaaS vendors "
                "across PDPA, GDPR, and SOC 2 dimensions for fiscal year 2025. "
                "4 vendors require remediation before Q1 2026 contract renewal."
            ),
            page_start=1,
            page_end=1,
        ),
        ExtractedSection(
            heading="APAC",
            level=3,
            heading_path=["2025 Annual Vendor Compliance Report", "Findings by Region", "APAC"],
            text=(
                "All 14 APAC vendors are compliant with PDPA Taiwan and Singapore PDPA. "
                "Two vendors (Vendor A, Vendor B) have outstanding sub-processor disclosures."
            ),
            page_start=2,
            page_end=2,
        ),
        ExtractedSection(
            heading="EU",
            level=3,
            heading_path=["2025 Annual Vendor Compliance Report", "Findings by Region", "EU"],
            text=(
                "12 of 13 EU vendors are GDPR-compliant. Vendor C lacks a Standard Contractual "
                "Clause for cross-border transfers and must be remediated by 2026-01-15."
            ),
            page_start=3,
            page_end=3,
        ),
        ExtractedSection(
            heading="Risk Matrix",
            level=2,
            heading_path=["2025 Annual Vendor Compliance Report", "Risk Matrix"],
            text="See Table 1 for the breakdown by severity.",
            page_start=4,
            page_end=4,
        ),
    ]
    tables = [
        ExtractedTable(
            index=0,
            page=4,
            has_header=True,
            caption="Table 1. Vendor risk matrix by region and severity.",
            rows=[
                ["Region", "Vendors", "High Risk", "Medium Risk", "Low Risk"],
                ["APAC", "14", "0", "2", "12"],
                ["EU", "13", "1", "0", "12"],
                ["Americas", "11", "0", "1", "10"],
                ["Total", "38", "1", "3", "34"],
            ],
        ),
    ]
    return ExtractedDocument(
        source_name="demo-vendor-compliance-2025.pdf",
        markdown=_MARKDOWN,
        sections=sections,
        tables=tables,
        page_count=4,
        metadata={"format": "pdf", "demo": True},
        warnings=[
            QualitySignal(
                code="ok",
                severity="info",
                message="No structural issues detected.",
            )
        ],
        extractor={"engine": "demo-fixture", "elapsed_ms": 0},
    )
