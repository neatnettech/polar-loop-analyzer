import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
from sqlalchemy.orm import Session
from src.infrastructure.database import FileImportDB, Database


class FileImportRecord:
    """Domain model for file import tracking."""

    def __init__(self, filename: str, file_path: str, file_size: int,
                 file_hash: str, file_type: str):
        self.filename = filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_hash = file_hash
        self.file_type = file_type
        self.import_date = datetime.now()
        self.records_imported = 0
        self.import_status = 'pending'
        self.error_message = None


class FileImportRepository:
    """Repository for tracking file imports."""

    def __init__(self, database: Database):
        self.db = database

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def get_file_type(self, filename: str) -> str:
        """Determine file type from filename."""
        if '247ohr' in filename:
            return 'heart_rate'
        elif 'activity' in filename:
            return 'activity'
        elif 'ppi_samples' in filename:
            return 'ppi'
        elif 'account' in filename:
            return 'account'
        elif 'sport-profiles' in filename:
            return 'sport_profiles'
        elif 'products-devices' in filename:
            return 'devices'
        elif 'calendar-items' in filename:
            return 'calendar'
        elif 'favourite-targets' in filename:
            return 'targets'
        else:
            return 'unknown'

    def is_file_imported(self, file_path: Path) -> bool:
        """Check if file has already been imported."""
        with self.db.get_session() as session:
            filename = file_path.name
            file_size = file_path.stat().st_size

            # Check by filename and size first (quick check)
            existing = session.query(FileImportDB).filter(
                FileImportDB.filename == filename,
                FileImportDB.file_size == file_size,
                FileImportDB.import_status == 'completed'
            ).first()

            if existing:
                # Verify with hash to ensure file hasn't changed
                current_hash = self.calculate_file_hash(file_path)
                return existing.file_hash == current_hash

            return False

    def get_new_files(self, data_directory: Path) -> List[Path]:
        """Get list of files that haven't been imported yet."""
        all_json_files = list(data_directory.glob("*.json"))
        new_files = []

        for file_path in all_json_files:
            if not self.is_file_imported(file_path):
                new_files.append(file_path)

        return new_files

    def record_import_start(self, file_path: Path) -> FileImportRecord:
        """Record the start of a file import."""
        filename = file_path.name
        file_size = file_path.stat().st_size
        file_hash = self.calculate_file_hash(file_path)
        file_type = self.get_file_type(filename)

        record = FileImportRecord(
            filename=filename,
            file_path=str(file_path),
            file_size=file_size,
            file_hash=file_hash,
            file_type=file_type
        )

        with self.db.get_session() as session:
            db_record = FileImportDB(
                filename=record.filename,
                file_path=record.file_path,
                file_size=record.file_size,
                file_hash=record.file_hash,
                import_date=record.import_date,
                file_type=record.file_type,
                records_imported=0,
                import_status='started'
            )
            session.add(db_record)
            session.commit()

        return record

    def record_import_completion(self, filename: str, records_imported: int,
                               status: str = 'completed', error_message: str = None):
        """Record the completion of a file import."""
        with self.db.get_session() as session:
            db_record = session.query(FileImportDB).filter(
                FileImportDB.filename == filename
            ).first()

            if db_record:
                db_record.records_imported = records_imported
                db_record.import_status = status
                db_record.error_message = error_message
                session.commit()

    def get_import_history(self) -> List[dict]:
        """Get history of all file imports."""
        with self.db.get_session() as session:
            records = session.query(FileImportDB).order_by(
                FileImportDB.import_date.desc()
            ).all()

            return [
                {
                    'filename': r.filename,
                    'file_type': r.file_type,
                    'import_date': r.import_date,
                    'records_imported': r.records_imported,
                    'status': r.import_status,
                    'file_size_kb': r.file_size // 1024
                }
                for r in records
            ]

    def get_import_stats(self) -> dict:
        """Get statistics about imports."""
        with self.db.get_session() as session:
            total_files = session.query(FileImportDB).count()
            completed_files = session.query(FileImportDB).filter(
                FileImportDB.import_status == 'completed'
            ).count()
            failed_files = session.query(FileImportDB).filter(
                FileImportDB.import_status == 'failed'
            ).count()

            total_records = session.query(FileImportDB).with_entities(
                FileImportDB.records_imported
            ).all()
            total_imported = sum(r[0] for r in total_records if r[0])

            return {
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'total_records_imported': total_imported
            }

    def remove_import_record(self, filename: str):
        """Remove import record (for re-importing)."""
        with self.db.get_session() as session:
            session.query(FileImportDB).filter(
                FileImportDB.filename == filename
            ).delete()
            session.commit()