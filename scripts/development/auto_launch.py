#!/usr/bin/env python3
"""Single-click zero-friction launcher for FinAuditPro.

Auto-bootstraps app data directories, executes DB schema migrations 1..9,
activates LM Studio local AI server background supervisor, and starts PySide6 GUI.
"""

import sys
from pathlib import Path

# Ensure src/ is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

def main() -> None:
    from finauditpro.__main__ import main as app_main
    from finauditpro.infrastructure.ai.lmstudio_supervisor import LMStudioSupervisor
    from finauditpro.infrastructure.first_run import bootstrap_app_data_dirs, initialize_database

    print("=================================================================")
    print(" FINAUDITPRO — ZERO-FRICTION SUPERVISED BACKGROUND LAUNCHER")
    print("=================================================================")

    # 1. Initialize environment & DB schema
    db_dir, docs_dir, vector_dir, _ = bootstrap_app_data_dirs()
    db_manager = initialize_database()
    print(f"  • Environment Data Roots: PASS ({db_dir.parent})")
    print(f"  • SQLite Database Schema: PASS ({db_manager.db_path})")

    # 2. Activate LM Studio Background Server Supervisor
    ai_status = LMStudioSupervisor.ensure_ai_server_ready(auto_start=True)
    if ai_status["is_online"]:
        print(f"  • Local LM Studio Server: ONLINE (Url: {ai_status['url']}, Action: {ai_status['action_taken']})")
        if ai_status["models_loaded"]:
            print(f"    Loaded Local AI Models: {', '.join(ai_status['models_loaded'])}")
    else:
        print(f"  • Local LM Studio Server: AIR-GAPPED FALLBACK (Offline on {ai_status['url']})")
        print("    [Auditor Note: FinAuditPro core audit calculations operate fully air-gapped without cloud dependencies]")

    print("=================================================================")
    print(" STARTING FINAUDITPRO DESKTOP APPLICATION...")
    print("=================================================================\n")

    # 3. Launch PySide6 Desktop GUI Interface
    app_main()

if __name__ == "__main__":
    main()
