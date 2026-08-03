"""One-time DB reset script — wipes all test data for clean client delivery."""
import os
import sys

appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
base = os.path.join(appdata, "FinAuditPro")

files_to_delete = [
    os.path.join(base, "finauditpro.db"),
    os.path.join(base, "sessions.json"),
    os.path.join(base, "audit_ledger.json"),
]

print(f"FinAuditPro data directory: {base}")
for fpath in files_to_delete:
    if os.path.exists(fpath):
        os.remove(fpath)    
        print(f"  DELETED: {fpath}")
    else:
        print(f"  NOT FOUND (already clean): {fpath}")

print("\nDatabase wiped. Fresh start on next launch.")
