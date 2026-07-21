"""
QR Verification Payload & Token Generator for FinAuditPro.
Generates verification payload data for embedding QR code security blocks in audit reports.
"""

from typing import Dict, Any, Optional
import json
import base64

class QRVerificationManager:
    """Generates QR verification payload data strings for reports."""

    @staticmethod
    def generate_verification_payload(
        report_id: str,
        client_name: str,
        gstin: str,
        document_hash: str,
        udin: Optional[str] = None
    ) -> Dict[str, Any]:
        """Constructs QR verification dictionary payload."""
        payload = {
            "system": "FinAuditPro Report Verification System",
            "report_id": report_id,
            "client_name": client_name,
            "gstin": gstin or "N/A",
            "document_hash_sha256": document_hash,
            "udin": udin or "N/A",
            "status": "VERIFIED_GENUINE"
        }
        return payload

    @staticmethod
    def generate_qr_string(payload_dict: Dict[str, Any]) -> str:
        """Converts payload dictionary to encoded verification string."""
        json_str = json.dumps(payload_dict, sort_keys=True)
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        return f"FINAUDITPRO://VERIFY?data={encoded}"
