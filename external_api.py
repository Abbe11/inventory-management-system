"""
Integration with the OpenFoodFacts public API.

OpenFoodFacts docs: https://world.openfoodfacts.org/data
- Product lookup by barcode: GET /api/v2/product/<barcode>.json
- Free-text search:          GET /cgi/search.pl?search_terms=<name>&json=1
"""
import requests

OFF_BASE_URL = "https://world.openfoodfacts.org"
DEFAULT_TIMEOUT = 10
# OpenFoodFacts requires a descriptive User-Agent identifying the app; requests
# without one (e.g. the default "python-requests/x.x") are frequently blocked
# with a 403. See https://openfoodfacts.github.io/openfoodfacts-server/api/
DEFAULT_HEADERS = {
    "User-Agent": "InventoryManagementSystem/1.0 (retail-lab-project)",
}


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API cannot be reached or returns bad data."""


def _normalize(product: dict, barcode: str = None) -> dict:
    return {
        "barcode": barcode or product.get("code"),
        "name": product.get("product_name") or product.get("generic_name") or "Unknown",
        "brand": product.get("brands"),
        "category": product.get("categories"),
        "image_url": product.get("image_url"),
    }


def get_product_by_barcode(barcode: str) -> dict | None:
    """Fetch a single product by its barcode. Returns None if not found."""
    url = f"{OFF_BASE_URL}/api/v2/product/{barcode}.json"
    try:
        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, headers=DEFAULT_HEADERS)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(str(exc)) from exc

    data = resp.json()
    if data.get("status") != 1:
        return None
    return _normalize(data["product"], barcode=barcode)


def search_products_by_name(name: str, page_size: int = 5) -> list:
    """Search OpenFoodFacts for products matching a free-text name."""
    url = f"{OFF_BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "json": 1,
        "page_s