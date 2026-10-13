"""Field schema definitions."""
from typing import Any, Type


class Field:
    def __init__(self, data_type: Type, required: bool = True, nullable: bool = False):
        self.data_type = data_type
        self.required = required
        self.nullable = nullable


class StringField(Field):
    def __init__(self, required: bool = True, nullable: bool = False):
        super().__init__(str, required=required, nullable=nullable)


class IntegerField(Field):
    def __init__(self, required: bool = True, nullable: bool = False):
        super().__init__(int, required=required, nullable=nullable)
