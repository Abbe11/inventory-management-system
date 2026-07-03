"""
Flask REST API for the retail Inventory Management System.

Routes
------
CRUD:
    GET    /items              list all inventory items
    POST   /items               create a new inventory item
    GET    /items/<id>          view one item
    PUT    /items/<id>          replace/update an item
    PATCH  /items/<id>          partially update an item
    DELETE /items/<id>          delete an item

Helper routes:
    GET  /items/search?q=<name>        search local inventory by name
    GET  /external/barcode/<barcode>   look up a product on OpenFoodFacts
    GET  /external/search?q=<name>     search OpenFoodFacts by name
    POST /items/import/<barcode>       fetch a product from OpenFoodFacts and
                                        add it straight into local inventory
    GET  /health                       basic health check
"""
import os

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from external_api import ExternalAPIError, get_product_by_barcode, search_products_by_name

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
default_db_uri = "sqlite:///" + os.path.join(BASE_DIR, "inventory.db")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", default_db_uri)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    barcode = db.Column(db.String(64), unique=False)
    brand = db.Column(db.String(120))
    category = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=0, nullable=False)
    price = db.Column(db.Float, default=0.0, nullable=False)
    image_url = db.Column(db.String(500))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "barcode": self.barcode,
            "brand": self.brand,
            "category": self.category,
            "quantity": self.quantity,
            "price": self.price,
            "image_url": self.image_url,
        }


def init_db():
    with app.app_context():
        db.create_all()


# ---------------------------------------------------------------- CRUD --- #

@app.route("/items", methods=["GET"])
def list_items():
    items = InventoryItem.query.all()
    return jsonify([i.to_dict() for i in items]), 200


@app.route("/items", methods=["POST"])
def create_item():
    payload = request.get_json(silent=True) or {}
    if not payload.get("name"):
        return jsonify({"error": "'name' is required"}), 400

    item = InventoryItem(
        name=payload["name"],
        barcode=payload.get("barcode"),
        brand=payload.get("brand"),
        category=payload.get("category"),
        quantity=payload.get("quantity", 0),
        price=payload.get("price", 0.0),
        image_url=payload.get("image_url"),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify(item.to_dict()), 200


@app.route("/items/<int:item_id>", methods=["PUT", "PATCH"])
def update_item(item_id):
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        return jsonify({"error": "item not found"}), 404

    payload = request.get_json(silent=True) or {}
    for field in ("name", "barcode", "brand", "category", "quantity", "price", "image_url"):
        if field in payload:
            setattr(item, field, payload[field])

    db.session.commit()
    return jsonify(item.to_dict()), 200


@app.route("/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        return jsonify({"error": "item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"item {item_id} deleted"}), 200


# ------------------------------------------------------------- Helpers --- #

@app.route("/items/search", methods=["GET"])
def search_items():
    query = request.args.get("q", "")
    items = InventoryItem.query.filter(InventoryItem.name.ilike(f"%{query}%")).all()
    return jsonify([i.to_dict() for i in items]), 200


@app.route("/external/barcode/<barcode>", methods=["GET"])
def external_by_barcode(barcode):
    try:
        product = get_product_by_barcode(barcode)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    if product is None:
        return jsonify({"error": "product not found on OpenFoodFacts"}), 404
    return jsonify(product), 200


@app.route("/external/search", methods=["GET"])
def external_by_name():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "query param 'q' is required"}), 400
    try:
        results = search_products_by_name(query)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(results), 200


@app.route("/items/import/<barcode>", methods=["POST"])
def import_item(barcode):
    """Fetch a product from OpenFoodFacts by barcode and store it locally."""
    try:
        product = get_product_by_barcode(barcode)
    except ExternalAPIError as exc:
        return jsonify({"error": str(exc)}), 502
    if product is None:
        return jsonify({"error": "product not found on OpenFoodFacts"}), 404

    payload = request.get_json(silent=True) or {}
    item = InventoryItem(
        name=product["name"],
        barcode=product["barcode"],
        brand=product["brand"],
        category=product["category"],
        image_url=product["image_url"],
        quantity=payload.get("quantity", 0),
        price=payload.get("price", 0.0),
    )
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run(debug=True)