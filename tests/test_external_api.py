"""Unit tests for the OpenFoodFacts integration, with requests fully mocked
out so the suite never depends on network access."""
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import external_api  # noqa: E402


@patch("external_api.requests.get")
def test_get_product_by_barcode_found(mock_get):
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Nutella",
            "brands": "Ferrero",
            "categories": "Spreads",
            "image_url": "http://example.com/n.png",
        },
    }
    mock_get.return_value = mock_resp

    result = external_api.get_product_by_barcode("3017620422003")
    assert result["name"] == "Nutella"
    assert result["barcode"] == "3017620422003"
    mock_get.assert_called_once()


@patch("external_api.requests.get")
def test_get_product_by_barcode_not_found(mock_get):
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {"status": 0}
    mock_get.return_value = mock_resp

    result = external_api.get_product_by_barcode("00000")
    assert result is None


@patch("external_api.requests.get")
def test_get_product_by_barcode_raises_on_network_error(mock_get):
    import requests

    mock_get.side_effect = requests.RequestException("boom")
    try:
        external_api.get_product_by_barcode("123")
        assert False, "expected ExternalAPIError"
    except external_api.ExternalAPIError:
        pass


@patch("external_api.requests.get")
def test_search_products_by_name(mock_get):
    mock_resp = Mock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "products": [
            {"code": "1", "product_name": "Peanut Butter", "brands": "X", "categories": "Spreads"},
            {"code": "2", "product_name": "Almond Butter", "brands": "Y", "categories": "Spreads"},
        ]
    }
    mock_get.return_value = mock_resp

    results = external_api.search_products_by_name("butter", page_size=5)
    assert len(results) == 2
    assert results[0]["name"] == "Peanut Butter"
