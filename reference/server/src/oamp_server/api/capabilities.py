"""Capabilities discovery endpoint for optional OAMP features."""

from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["Capabilities"])


@router.get("/capabilities")
async def get_capabilities() -> dict[str, object]:
    """Advertise optional OAMP capabilities supported by the reference backend."""
    return {
        "oamp_version": "1.2.0",
        "capabilities": {
            "streaming": {
                "supported": False,
                "filter_keys": ["user_id", "event_type", "sensitivity_class", "governance_label"],
            },
            "as_of": {
                "supported": False,
            },
            "governance": {
                "supported": True,
                "sensitivity_classes": ["public", "internal", "confidential", "restricted"],
                "labels_supported": True,
                "extended_provenance_supported": True,
                "withheld_stub_support": False,
            },
            "user_id_format": {
                "description": "opaque string",
            },
            "id_preservation": "preserved",
            "content_types": ["application/json"],
            "auth_schemes": [],
        },
    }
