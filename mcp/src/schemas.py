"""Reusable output-schema helpers.

Output schemas are permissive (``additionalProperties: true``, only ``success``
required) so the shared error envelope ``{success: false, error: ...}`` validates
against the same schema — strict clients reject results whose structured content does
not conform to the declared ``outputSchema``. Mirrors ``openlca_mcp/src/schemas.py``.
"""

from __future__ import annotations

from typing import Optional


def arr(items: dict) -> dict:
    return {"type": "array", "items": items}


def out(properties: Optional[dict] = None) -> dict:
    """Build a strict-but-permissive tool output schema (``success`` + fields)."""
    props = {"success": {"type": "boolean"}}
    if properties:
        props.update(properties)
    return {
        "type": "object",
        "properties": props,
        "required": ["success"],
        "additionalProperties": True,
    }
