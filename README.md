# Inventory Management System

A Flask REST API + CLI admin portal for a small retail company's inventory,
with real-time product enrichment from the [OpenFoodFacts API](https://world.openfoodfacts.org/data).

## Problem

Employees need a way to add, edit, view, and delete inventory items, and to
pull in product details (name, brand, category, image) by barcode or name
instead of typing them in by hand.

## Design

- **API** (`app.py`): Flask + Flask-SQLAlchemy, backed by SQLite (`inventory.db`).
  Exposes CRUD routes plus helper routes for local search and OpenFoodFacts lookups.
- **External API** (`external_api.py`): thin wrapper around OpenFoodFacts'
  barcode-lookup and free-text search endpoints. Isolated in its own module so
  it can be unit-tested without hitting the network.
- **CLI** (`cli.py`): argparse-based client that talks to the running Flask
  API over HTTP — the same interface an employee's browser or Postman would use.
- **Tests** (`tests/`): pytest suite covering CRUD routes, helper routes, the
  external API wrapper, and the CLI, all with the network mocked out.

```
inventory_api/
├── app.py             Flask app: models + routes
├── external_api.py     OpenFoodFacts integration
├── cli.py              CLI client
├── requirements.txt
└── tests/
    ├── conftest.py
    ├── test_app.py
    ├── test_external_api.py
    └── test_cli.py
```

## Setup

```bash
cd inventory_api
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python app.py                                       # starts on http://127.0.0.1:5000
```

## API Reference

| Method | Route                          | Description                                   |
|--------|---------------------------------|------------------------------------------------|
| GET    | `/items`                        | List all inventory items                       |
| POST   | `/items`                        | Create an item (`name` required)                |
| GET    | `/items/<id>`                   | View one item                                   |
| PUT    | `/items/<id>`                   | Replace an item's fields                        |
| PATCH  | `/items/<id>`                   | Partially update an item                        |
| DELETE | `/items/<id>`                   | Delete an item                                  |
| GET    | `/items/search?q=<name>`        | Search local inventory by name                  |
| GET    | `/external/barcode/<barcode>`   | Look up a product on OpenFoodFacts by barcode   |
| GET    | `/external/search?q=<name>`     | Search OpenFoodFacts by name                    |
| POST   | `/items/import/<barcode>`       | Fetch from OpenFoodFacts and add to inventory   |
| GET    | `/health`                       | Health check                                    |

Example:

```bash
curl -X POST http://127.0.0.1:5000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Peanut Butter", "quantity": 10, "price": 4.99}'

curl "http://127.0.0.1:5000/external/barcode/3017620422003"

curl -X POST http://127.0.0.1:5000/items/import/3017620422003 \
  -H "Content-Type: application/json" \
  -d '{"quantity": 5, "price": 3.49}'
```

## CLI Usage

With the API running in one terminal, use the CLI from another:

```bash
python cli.py list
python cli.py view 1
python cli.py add --name "Peanut Butter" --quantity 10 --price 4.99
python cli.py update 1 --quantity 25
python cli.py delete 1
python cli.py search-local --name butter
python cli.py search-external --barcode 3017620422003
python cli.py search-external --name nutella
python cli.py import 3017620422003 --quantity 5 --price 3.49
```

Set `API_URL` to point the CLI at a different host/port than the default
`http://127.0.0.1:5000`.

## Testing

```bash
pip install -r requirements.txt
pytest -v
```

The suite mocks all outbound HTTP calls (both to OpenFoodFacts and, for the
CLI tests, to the Flask API itself), so it runs offline and deterministically.
It covers: every CRUD route (happy path + 404/400 cases), the local search
route, the external barcode/name lookup routes (found/not-found/error),
the import-to-inventory route, the `external_api` module in isolation, and
the CLI's argument parsing and outgoing requests.

## Git Workflow

This repo was built using a feature-branch workflow:

- `feature/crud-api` — Flask app, model, CRUD routes
- `feature/external-api` — OpenFoodFacts integration + helper/import routes
- `feature/cli` — CLI client
- `feature/tests` — pytest suite
- `feature/docs` — README

Each branch was merged into `main` and deleted after merge. To push this
history to your own GitHub repo:

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

## Maintenance Notes

- Swap SQLite for Postgres/MySQL by changing `DATABASE_URL`; no code changes needed.
- OpenFoodFacts occasionally returns partial data (missing brand/category/image);
  the API passes these through as `null` rather than failing.
- Add authentication (e.g. Flask-Login or a bearer token) before exposing this
  API outside a trusted internal network — it currently has none.
