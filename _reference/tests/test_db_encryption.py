"""
Unit & Integration Tests for Live Database Encryption and SQLCipher Migration.
"""

import unittest
import tempfile
import os
import shutil

from database.database import init_db, get_session, HAS_SQLCIPHER
from database.db_encryptor import EncryptExistingDatabase
from database.models import Client, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestDatabaseEncryption(unittest.TestCase):

    def setUp(self):
        init_db()

    def test_database_header_detection(self):
        """Verify plain SQLite header detection vs encrypted DB state."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_plain_db = os.path.join(temp_dir, "plain.db")
            # Write standard SQLite header
            with open(sample_plain_db, "wb") as f:
                f.write(b"SQLite format 3\x00" + b"\x00" * 100)

            # Plain SQLite database should NOT be detected as encrypted
            self.assertFalse(EncryptExistingDatabase.is_database_encrypted(sample_plain_db))

            sample_enc_db = os.path.join(temp_dir, "enc.db")
            # Write arbitrary encrypted bytes
            with open(sample_enc_db, "wb") as f:
                f.write(b"\x9f\x12\x88\x34\x11\x42" + b"\x00" * 100)

            # Encrypted database file should be detected as encrypted
            self.assertTrue(EncryptExistingDatabase.is_database_encrypted(sample_enc_db))

    def test_get_session_transaction(self):
        """Verify get_session context manager functions cleanly for CRUD operations."""
        import uuid
        client_name = f"Encrypted DB Test Client {uuid.uuid4().hex[:6]}"
        with get_session() as session:
            client = Client(name=client_name, gst_number="27AAAAA0000A1Z5")
            session.add(client)

        with get_session() as session:
            fetched = session.query(Client).filter_by(name=client_name).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.name, client_name)

    def test_encryptor_run_idempotent(self):
        """Verify EncryptExistingDatabase.run handles missing files or existing state gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_db = os.path.join(temp_dir, "nonexistent.db")
            res = EncryptExistingDatabase.run(fake_db, temp_dir)
            self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
