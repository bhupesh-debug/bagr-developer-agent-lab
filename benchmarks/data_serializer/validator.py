"""Schema validation logic."""
from typing import Any, Dict
from schema import Field


class ValidationError(Exception):
    pass


class SchemaValidator:
    def __init__(self, fields: Dict[str, Field]):
        self.fields = fields

    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cleaned: Dict[str, Any] = {}

        for name, field in self.fields.items():
            if name not in payload:
                if field.required:
                    raise ValidationError(f"Missing required field: {name}")
                continue

            val = payload[name]

            # Logic Bug: Checks required instead of field.nullable for None values
            if val is None:
                if not field.required:  # BUG: should check if field.nullable
                    cleaned[name] = None
                    continue
                else:
                    raise ValidationError(f"Field {name} cannot be None")

            if not isinstance(val, field.data_type):
                raise ValidationError(f"Field {name} expected {field.data_type.__name__}, got {type(val).__name__}")

            cleaned[name] = val

        return cleaned
