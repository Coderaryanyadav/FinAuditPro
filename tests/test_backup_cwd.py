import sys
import os

# We will run this script from C:\
# So we need to point sys.path to the absolute path of src
src_path = r"c:\Users\Jeet Shah\OneDrive\Desktop\1 - FinAuditPro\src"
sys.path.append(src_path)

from security.backup import BackupEngine
from database.database import DB_PATH
from core.config import get_default_data_dir

def run_test():
    # Make sure we have a db
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f:
            f.write("Dummy DB content")
    
    docs_dir = os.path.join(get_default_data_dir(), "documents")
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "test_doc.txt"), "w") as f:
        f.write("Dummy document")

    be = BackupEngine()
    
    print("Creating backup...")
    # Passing None uses absolute defaults
    archive = be.create_backup(db_path=None, docs_dir=None)
    print("Backup created at:", archive.file_path)
    
    assert os.path.isabs(archive.file_path), "Backup path is not absolute"
    assert os.path.exists(archive.file_path), "Backup file does not exist"
    
    print("Restoring backup...")
    target_db = os.path.join(get_default_data_dir(), "restore_db_test.db")
    target_docs = os.path.join(get_default_data_dir(), "restore_docs_test")
    
    success = be.restore_backup(archive.file_path, target_db_path=target_db, target_docs_dir=target_docs)
    
    print("Restore success:", success)
    assert success
    assert os.path.exists(target_db)
    assert os.path.exists(target_docs)
    
    print("Backup and Restore paths are absolute and function correctly from alternate CWD.")

if __name__ == "__main__":
    run_test()
