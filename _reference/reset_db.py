"""One-time DB reset script — wipes all test data for clean client delivery."""
import os
import sys

# Ensure src/ is in sys.path
sys_path_root = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(sys_path_root, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from core.config import get_default_data_dir
    base = get_default_data_dir()
except Exception:
    appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
    base = os.path.join(appdata, "FinAuditPro")

files_to_delete = [
    os.path.join(base, "finauditpro.db"),
    os.path.join(base, "finauditpro.db-journal"),
    os.path.join(base, "sessions.json"),
    os.path.join(base, "audit_ledger.json"),
    os.path.join(base, ".login_lockouts.json"),
    os.path.join(base, ".revoked_tokens.json"),
    os.path.join("data", "finauditpro.db"),
    os.path.join("data", "finauditpro.db-journal"),
    os.path.join("data", ".login_lockouts.json"),
]

print(f"FinAuditPro data directory: {base}")
for fpath in files_to_delete:
    if os.path.exists(fpath):
        try:
            os.remove(fpath)    
            print(f"  DELETED: {fpath}")
        except Exception as err:
            print(f"  COULD NOT DELETE ({err}): {fpath}")
    else:
        print(f"  NOT FOUND (already clean): {fpath}")

print("\nDatabase wipe attempt finished.")

