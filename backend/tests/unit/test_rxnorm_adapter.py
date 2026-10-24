"""RxNorm adapter tests — mocked HTTP; no network required."""

from __future__ import annotations

from unittest.mock import patch

from backend.app.services.rxnorm_adapter import search_rxnorm


def test_search_rxnorm_parses_exact_and_does_not_fabricate():
    def fake_get(path, params=None):
        if path == "/rxcui.json":
            return {"idGroup": {"rxnormId": ["161"]}}
        if path.startswith("/rxcui/161/properties"):
            return {"properties": {"rxcui": "161", "name": "Acetaminophen", "tty": "IN"}}
        if path.startswith("/rxcui/161/related"):
            return {
                "relatedGroup": {
                    "conceptGroup": [
                        {
                            "tty": "IN",
                            "conceptProperties": [{"rxcui": "161", "name": "Acetaminophen"}],
                        }
                    ]
                }
            }
        if path == "/approximateTerm.json":
            return {"approximateGroup": {"candidate": []}}
        return {}

    with patch("backend.app.services.rxnorm_adapter._get_json_sync", side_effect=fake_get):
        # Clear cache between runs by using unique query padding once
        result = search_rxnorm("paracetamol-test-mock")
        assert result["exact"]
        assert result["exact"][0]["source_record_id"] == "161"
        assert result["exact"][0]["verification_status"] in {
            "SOURCE_BACKED",
            "PARTIALLY_VERIFIED",
        }
        assert result["exact"][0]["is_synthetic"] is False


def test_search_rxnorm_empty_message():
    def fake_get(path, params=None):
        if path == "/rxcui.json":
            return {"idGroup": {}}
        if path == "/approximateTerm.json":
            return {"approximateGroup": {"candidate": []}}
        return {}

    with patch("backend.app.services.rxnorm_adapter._get_json_sync", side_effect=fake_get):
        result = search_rxnorm("zzznomatchxyz-mock")
        assert result["exact"] == []
        assert result["suggestions"] == []
        assert "No suitable match" in (result["message"] or "")
