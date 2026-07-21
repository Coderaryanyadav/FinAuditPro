"""
Crash Recovery & Session Autosave Manager for FinAuditPro.
Saves session state, open documents, and current engagement context to survive unexpected crashes.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    user_email: str
    active_engagement_id: Optional[int]
    active_screen_index: int = 0
    open_documents: List[str] = field(default_factory=list)
    last_saved: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_email": self.user_email,
            "active_engagement_id": self.active_engagement_id,
            "active_screen_index": self.active_screen_index,
            "open_documents": self.open_documents,
            "last_saved": self.last_saved.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        return cls(
            user_email=data.get("user_email", "unknown"),
            active_engagement_id=data.get("active_engagement_id"),
            active_screen_index=data.get("active_screen_index", 0),
            open_documents=data.get("open_documents", []),
            last_saved=datetime.fromisoformat(data["last_saved"]) if data.get("last_saved") else datetime.utcnow()
        )


class CrashRecoveryManager:
    """Manages periodic session state autosaving and crash recovery restoration."""

    def __init__(self, state_file_path: str = "data/session_autosave.json"):
        self.state_file_path = state_file_path
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

    def autosave_session(self, state: SessionState) -> bool:
        """Autosave session state to local disk."""
        try:
            state.last_saved = datetime.utcnow()
            with open(self.state_file_path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)
            logger.debug(f"Autosaved session state to {self.state_file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to autosave session state: {e}")
            return False

    def recover_session(self) -> Optional[SessionState]:
        """Loads and recovers crashed session state if available."""
        if not os.path.exists(self.state_file_path):
            return None

        try:
            with open(self.state_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = SessionState.from_dict(data)
            logger.info(f"Recovered crashed session for user {state.user_email} at screen index {state.active_screen_index}")
            return state
        except Exception as e:
            logger.error(f"Failed to recover session state: {e}")
            return None

    def clear_recovery_state(self) -> None:
        """Clear autosave state on clean shutdown."""
        if os.path.exists(self.state_file_path):
            try:
                os.remove(self.state_file_path)
            except Exception as e:
                logger.warning(f"Could not remove autosave state file: {e}")
