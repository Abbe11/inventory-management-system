#!/usr/bin/env python3
"""
CLI for the Inventory Management System.

Talks to the Flask API over HTTP (set API_URL env var to override the
default http://127.0.0.1:5000).

Examples
--------
    python cli.py list
    python cli.py view 1
    python cli.py add --name "Peanut Butter" --quantity 10 --price 4.99
    python cli.py update 1 --quantity 25
    python cli.py delete 1
    python cli.py search-local --name butter
    python cli.py search-external --barcode 3017620422003
    python cli.py search-external --name nutella
    python cli.py import 3017620422003 --quantity 5 --price 3.49
"""
import argparse
import os
import sys

import requests

API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000")


def _print(payload):
    import json
    print(json.dumps(payload, indent=2))


def cmd_list(_args):
    resp = requests.get(f"{API_URL}/items")
    _print(resp.json())


def cmd_view(args):
    resp = requests.get(f"{API_URL}/items/{args.id}")
    _print(resp.json())


def cmd_add(args):
    body = {
        "name": args.name,
        "barcode": args.barcode,
        "brand": args.brand,
        "category": args.category,
        "quantity": args.quantity,
        "price": args.price,
        "image_url": args.image_url,
    }
    body = {k: v for k, v in body.items() if v is not None}
    resp = requests.post(f"{API_URL}/items", json=body)
    _print(resp.json())


def cmd_update(args):
    body = {}
    for field in ("name", "barcode", "brand", "category", "quantity", "price", "image_url"):
        value = getattr(args, field)
        if value is not None:
            body[field] = value
    resp = requests.patch(f"{API_URL}/items/{args.id}", json=body)
    _print(resp.json())


def cmd_delete(args):
    resp = requests.delete(f"{API_URL}/items/{args.id}")
    _print(resp.json())


def cmd_search_local(args):
    resp = requests.get(f"{API_URL}/items/search", params={"q": args.name})
    _print(resp.json())


def cmd_search_external(args):
    if args.barcode:
        resp = requests.get(f"{API_URL}/external/barcode/{args.barcode}")
    elif args.name:
        resp = requests.get(f"{API_URL}/external/search", params={"q": args.name})
    else:
        print("Provide --barcode or --name", file=sys.stderr)
        sys.exit(1)
    _print(resp.json())


def cmd_import(args):
    body = {"quantity": args.quantity, "price": args.price}
    resp = requests.post(f"{API_URL}/items/import/{args.barcode}", json=body)
    _print(resp.json())


def build_parser():
    parser = argparse.ArgumentParser(description="Inventory Management CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List all inventory items").set_defaults(func=cmd_list)

    p = sub.add_parser("view", help="View one item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_view)

    p = sub.add_parser("add", help="Add a new inventory item")
    p.add_argument("--name", required=True)
    p.add_argument("--barcode")
    p.add_argument("--brand")
    p.add_argument("--category")
    p.add_argument("--quantity", type=int, default=0)
    p.add_argument("--price", type=float, default=0.0)
    p.add_argument("--image-url", dest="image_url")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", help="Update an existing item")
    p.add_argument("id", type=int)
    p.add_argument("--name")
    p.add_argument("--barcode")
    p.add_argument("--brand")
    p.add_argument("--category")
    p.add_argument("--quantity", type=int)
    p.add_argument("--price", type=float)
    p.add_argument("--image-url", dest="image_url")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="Delete an item")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("search-local", help="Search local inventory by name")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_search_local)

    p = sub.add_parser("search-external", help="Search OpenFoodFacts")
    p.add_argument("--barcode")
    p.add_argument("--name")
    p.set_defaults(func=cmd_search_external)

    p = sub.add_parser("import", help="Import a product from OpenFoodFacts into inventory")
    p.add_argument("barcode")
    p.add_argument("--quantity", type=int, default=0)
    p.add_argument("--price", type=float, default=0.0)
    p.set_defaults(func=cmd_import)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
