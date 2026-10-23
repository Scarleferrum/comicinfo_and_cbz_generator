"""Small dependency-free metadata model and Excel value normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .fields_v2_5 import FIELD_BY_KEY, FIELDS


def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, float) and value != value)


def normalize_value(key: str, value: Any) -> str:
    if _empty(value):
        return ""
    field = FIELD_BY_KEY.get(key)
    if field and field.integer:
        try:
            return str(int(float(value)))
        except (TypeError, ValueError, OverflowError):
            pass
    return str(value).strip()


@dataclass
class ComicMetadata:
    values: dict[str, str]

    def __init__(self, values: Mapping[str, Any] | None = None):
        incoming = values or {}
        self.values = {}
        for field in FIELDS:
            value = incoming.get(field.key)
            if _empty(value):
                value = field.default
            self.values[field.key] = normalize_value(field.key, value)

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default)

    def as_dict(self) -> dict[str, str]:
        return dict(self.values)

    def __getitem__(self, key: str) -> str:
        return self.values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.values[key] = normalize_value(key, value)
