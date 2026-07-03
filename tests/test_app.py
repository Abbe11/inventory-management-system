"""Route-level tests for the Flask inventory API (CRUD + helper routes)."""
from unittest.mock import patch


def _create_sample_item(client, **overrides):
    body = {"name": "Sample Soup", "quantity": 5, "price": 2.50}
    body.update(overrides)
    resp = client.post("/items", json=body)
    return resp


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_create_item(client):
    resp = _create_sample_item(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Sample Soup"
    assert data["quantity"] == 5
    assert "id" in data


def test_create_item_requires_name(client):
    resp = client.post("/items", json={"quantity": 1})
    assert resp.status_code == 400


def test_list_items(client):
    _create_sample_item(client)
    _create_sample_item(client, name="Second Item")
    resp = client.get("/items")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2


def test_get_item(client):
    created = _create_sample_item(client).get_json()
    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Sample Soup"


def test_get_item_not_found(client):
    resp = client.get("/items/999")
    assert resp.status_code == 404


def test_update_item_patch(client):
    created = _create_sample_item(client).get_json()
    resp = client.patch(f"/items/{created['id']}", json={"quantity": 20})
    assert resp.status_code == 200
    assert resp.get_json()["quantity"] == 20
    assert resp.get_json()["name"] == "Sample Soup"  # unchanged


def test_update_item_put(client):
    created = _create_sample_item(client).get_json()
    resp = client.put(
        f"/items/{created['id']}",
        json={"name": "Renamed", "quantity": 1, "price": 9.99},
    )
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Renamed"


def test_update_item_not_found(client):
    resp = client.patch("/items/999", json={"quantity": 1})
    assert resp.status_code == 404


def test_delete_item(client):
    created = _create_sample_item(client).get_json()
    resp = client.delete(f"/items/{created['id']}")
    assert resp.status_code == 200
    resp = client.get(f"/items/{created['id']}")
    assert resp.status_code == 404


def test_delete_item_not_found(client):
    resp = client.delete("/items/999")
    assert resp.status_code == 404


def test_search_local(client):
    _create_sample_item(client, name="Tomato Soup")
    _create_sample_item(client, name="Chicken Noodle")
    resp = client.get("/items/search", query_string={"q": "soup"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Tomato Soup"


@patch("app.get_product_by_barcode")
def test_external_by_barcode_found(mock_lookup, client):
    mock_lookup.return_value = {
        "barcode": "12345",
        "name": "Mock Cereal",
        "brand": "MockBrand",
        "category": "Breakfast",
        "image_url": "http://example.com/img.png",
    }
    resp = client.get("/external/barcode/12345")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Mock Cereal"
    mock_lookup.assert_called_once_with("12345")


@patch("app.get_product_by_barcode")
def test_external_by_barcode_not_found(mock_lookup, client):
    mock_lookup.return_value = None
    resp = client.get("/external/barcode/00000")
    assert resp.status_code == 404


@patch("app.search_products_by_name")
def test_external_search_by_name(mock_search, client):
    mock_search.return_value = [
        {"barcode": "1", "name": "Peanut Butter", "brand": "X", "category": "Spreads", "image_url": None}
    ]
    resp = client.get("/external/search", query_string={"q": "peanut butter"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["name"] == "Peanut Butter"


def test_external_search_requires_query(client):
    resp = client.get("/external/search")
    assert resp.status_code == 400


@patch("app.get_product_by_barcode")
def test_import_item_adds_to_inventory(mock_lookup, client):
    mock_lookup.return_value = {
        "barcode": "3017620422003",
        "name": "Nutella",
        "brand": "Ferrero",
        "category": "Spreads",
        "image_url": "http://example.com/nutella.png",
    }
    resp = client.post("/items/import/3017620422003", json={"quantity": 3, "price": 4.99})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Nutella"
    assert data["quantity"] == 3

    # confirm it is now retrievable from the local inventory
    listing = client.get("/items").get_json()
    assert any(item["barcode"] == "3017620422003" for item in listing)


@patch("app.get_product_by_barcode")
def test_import_item_not_found_upstream(mock_lookup, client):
    mock_lookup.return_value = None
    resp = client.post("/items/import/00000", json={})
    assert resp.status_code == 404
