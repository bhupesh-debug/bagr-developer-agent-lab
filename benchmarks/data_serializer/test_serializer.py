"""Unit tests for schema validator."""
import pytest
from schema import IntegerField, StringField
from validator import SchemaValidator, ValidationError


def test_valid_payload():
    validator = SchemaValidator({
        "username": StringField(required=True),
        "age": IntegerField(required=True),
    })
    cleaned = validator.validate({"username": "alice", "age": 30})
    assert cleaned["username"] == "alice"
    assert cleaned["age"] == 30


def test_required_nullable_field():
    """Fails initially: required=True with nullable=True should allow None, but validator rejected it."""
    validator = SchemaValidator({
        "title": StringField(required=True, nullable=True),
        "score": IntegerField(required=False, nullable=False),
    })
    # When title is provided as None, it must be allowed because nullable=True
    cleaned = validator.validate({"title": None})
    assert cleaned["title"] is None
