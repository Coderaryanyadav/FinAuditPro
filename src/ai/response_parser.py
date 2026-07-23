import json
import re
from typing import Dict, Any
from .json_schema import AuditFindingSchema
from core.exceptions import FinAuditError

class JSONParseError(FinAuditError):
    pass

class ResponseParser:
    """
    Validates and repairs LLM JSON output.
    Ensures strict adherence to AuditFindingSchema.
    """

    @classmethod
    def extract_json(cls, raw_response: str) -> str:
        """Extracts JSON block if the LLM wrapped it in markdown."""
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        if match:
            return match.group(1)
            
        # Try to find the first { and last }
        start = raw_response.find('{')
        end = raw_response.rfind('}')
        if start != -1 and end != -1 and end > start:
            return raw_response[start:end+1]
            
        return raw_response

    @classmethod
    def repair_json(cls, json_str: str) -> str:
        """Attempt basic repairs on malformed JSON (e.g. trailing commas)."""
        # Remove trailing commas
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        return json_str

    @classmethod
    def parse_audit_finding(cls, raw_response: str) -> Dict[str, Any]:
        """Parse, repair, and validate against the Pydantic schema."""
        json_str = cls.extract_json(raw_response)
        json_str = cls.repair_json(json_str)
        
        try:
            data = json.loads(json_str)
            # Validate using Pydantic
            validated = AuditFindingSchema(**data)
            return validated.dict()
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Failed to parse LLM response into JSON. Raw: {raw_response[:100]}...") from e
        except (ValueError, KeyError, TypeError) as e: # Catch Pydantic validation errors
            raise JSONParseError(f"LLM Response failed schema validation: {e}")
