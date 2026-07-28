"""Reusable output-schema helpers.

Output schemas are permissive (``additionalProperties: true``, only ``success``
required) so the shared error envelope ``{success: false, error: ...}`` validates
against the same schema â€” strict clients reject results whose structured content does
not conform to the declared ``outputSchema``. Mirrors ``openlca_mcp/src/schemas.py``.
"""

from __future__ import annotations

from typing import Optional
