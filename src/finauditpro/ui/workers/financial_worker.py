"""Asynchronous PySide6 worker thread for financial dataset import and analytics execution."""

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from finauditpro.application.services.financial_service import FinancialService, ImportDatasetDTO
from finauditpro.domain.financial_entities import DatasetTypeEnum


class FinancialImportWorker(QThread):
    """QThread running dataset ingestion and column normalization off the UI thread."""

    import_started = Signal(str)
    import_progress = Signal(str, int, int)
    import_completed = Signal(object)
    import_failed = Signal(str, str)

    def __init__(
        self,
        financial_service: FinancialService,
        engagement_id: str,
        file_path: str,
        dataset_type: DatasetTypeEnum = DatasetTypeEnum.GENERAL_LEDGER,
        custom_mappings: dict[str, str] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.financial_service = financial_service
        self.engagement_id = engagement_id
        self.file_path = file_path
        self.dataset_type = dataset_type
        self.custom_mappings = custom_mappings or {}

    def run(self) -> None:
        filename = Path(self.file_path).name
        self.import_started.emit(filename)
        self.import_progress.emit("Reading Rows & Validating", 0, 1)

        try:
            dto = ImportDatasetDTO(
                engagement_id=self.engagement_id,
                file_path=self.file_path,
                dataset_type=self.dataset_type,
                custom_mappings=self.custom_mappings,
            )

            ds = self.financial_service.import_dataset(dto)
            self.import_progress.emit("Import Complete", ds.valid_rows, ds.total_rows)
            self.import_completed.emit(ds)

        except Exception as ex:
            self.import_failed.emit(filename, str(ex))
