"""Tests for the optional capabilities discovery endpoint."""

from __future__ import annotations


class TestCapabilities:
    async def test_capabilities_endpoint(self, client):
        resp = await client.get("/v1/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["oamp_version"] == "1.2.0"
        governance = data["capabilities"]["governance"]
        assert governance["supported"] is True
        assert governance["extended_provenance_supported"] is True
        assert governance["withheld_stub_support"] is False
