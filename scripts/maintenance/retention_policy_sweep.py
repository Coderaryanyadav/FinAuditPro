#!/usr/bin/env python3
"""Statutory retention policy inspector for SQC 1 and SA 230 audit documentation retain-until dates."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.archival_models import (
    EngagementArchiveModel,
    RetentionConfigModel,
)


def sweep_retention_policies() -> None:
    db_manager = initialize_database()
    now_utc = datetime.now(UTC)
    print(f"Executing SQC 1 retention policy sweep at {now_utc.isoformat()}...")

    with db_manager.session_scope() as session:
        policies = session.query(RetentionConfigModel).all()
        archives = session.query(EngagementArchiveModel).all()


        print(f"\nFound {len(archives)} sealed engagement archive(s) and {len(policies)} retention policy rule(s).")
        for arch in archives:
            status = "ACTIVE RETENTION"
            if arch.retain_until:
                retain_dt = arch.retain_until
                if retain_dt.tzinfo is None:
                    retain_dt = retain_dt.replace(tzinfo=UTC)
                if now_utc >= retain_dt:
                    status = "ELIGIBLE FOR STATUTORY DISPOSAL"
                print(f"  • Engagement ID: {arch.engagement_id} | Retain Until: {arch.retain_until.isoformat()} | Status: {status}")
            else:
                print(f"  • Engagement ID: {arch.engagement_id} | Retain Until: INDEFINITE | Status: {status}")

    print("\nRetention policy sweep completed.")


if __name__ == "__main__":
    sweep_retention_policies()
