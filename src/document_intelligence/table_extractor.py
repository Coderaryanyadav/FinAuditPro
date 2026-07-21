"""
Table Extraction Module for FinAuditPro.
Parses structured tables from PDF, Excel, and CSV financial documents.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import csv
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractedTable:
    page_number: int
    headers: List[str]
    rows: List[List[Any]]
    num_rows: int = 0
    num_cols: int = 0

    def __post_init__(self):
        self.num_rows = len(self.rows)
        self.num_cols = len(self.headers) if self.headers else (len(self.rows[0]) if self.rows else 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "headers": self.headers,
            "rows": self.rows,
            "num_rows": self.num_rows,
            "num_cols": self.num_cols,
        }


class TableExtractor:
    """Extracts tabular ledger and invoice data from PDF, Excel, and CSV documents."""

    @classmethod
    def extract_tables_from_pdf(cls, file_path: str) -> List[ExtractedTable]:
        """Extract tables from PDF using pdfplumber if available, fallback to empty list."""
        tables = []
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages, start=1):
                    page_tables = page.extract_tables()
                    for tbl in page_tables:
                        if not tbl or len(tbl) < 2:
                            continue
                        headers = [str(c or "").strip() for c in tbl[0]]
                        rows = [[str(cell or "").strip() for cell in row] for row in tbl[1:]]
                        tables.append(ExtractedTable(page_number=idx, headers=headers, rows=rows))
        except ImportError:
            logger.warning("pdfplumber not installed. PDF table extraction skipped.")
        except Exception as e:
            logger.error(f"Failed PDF table extraction for {file_path}: {e}")
        return tables

    @classmethod
    def extract_tables_from_csv(cls, file_path: str) -> List[ExtractedTable]:
        """Extract table from CSV file."""
        tables = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                all_rows = list(reader)
                if len(all_rows) >= 2:
                    headers = [str(c).strip() for c in all_rows[0]]
                    rows = [[str(cell).strip() for cell in r] for r in all_rows[1:]]
                    tables.append(ExtractedTable(page_number=1, headers=headers, rows=rows))
        except Exception as e:
            logger.error(f"Failed CSV table extraction for {file_path}: {e}")
        return tables

    @classmethod
    def extract_tables_from_excel(cls, file_path: str) -> List[ExtractedTable]:
        """Extract tables from Excel workbook (.xlsx / .xls)."""
        tables = []
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            for idx, sheet_name in enumerate(excel_file.sheet_names, start=1):
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                df = df.fillna("")
                headers = [str(c).strip() for c in df.columns]
                rows = df.astype(str).values.tolist()
                tables.append(ExtractedTable(page_number=idx, headers=headers, rows=rows))
        except ImportError:
            logger.warning("pandas / openpyxl not installed. Excel table extraction skipped.")
        except Exception as e:
            logger.error(f"Failed Excel table extraction for {file_path}: {e}")
        return tables

    @classmethod
    def extract_tables(cls, file_path: str) -> List[ExtractedTable]:
        """Unified table extraction router based on file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.extract_tables_from_pdf(file_path)
        elif ext in [".xlsx", ".xls"]:
            return cls.extract_tables_from_excel(file_path)
        elif ext == ".csv":
            return cls.extract_tables_from_csv(file_path)
        return []
