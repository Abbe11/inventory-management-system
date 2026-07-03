"""Tests for the CLI argument parsing and its HTTP calls (requests mocked)."""
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import cli  # noqa: E402


@patch("cli.requests.get")
def test_cmd_list_calls_items_endpoint(mock_get, capsys):
    mock_get.return_value = Mock(json=lambda: [])
    args = cli.build_parser().parse_args(["list"])
    args.func(args)
    mock_get.assert_called_once_with(f"{cli.API_URL}/items")


@patch("cli.requests.post")
def test_cmd_add_posts_expected_body(mock_post):
    mock_post.return_value = Mock(json=lambda: {"id": 1, "name": "Milk"})
    args = cli.build_parser().parse_args(
        ["add", "--name", "Milk", "--quantity", "2", "--price", "3.5"]
    )
    args.func(args)
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["name"] == "Milk"
    assert kwargs["json"]["quantity"] == 2


@patch("cli.requests.delete")
def test_cmd_delete_calls_correct_url(mock_delete):
    mock_delete.return_value = Mock(json=lambda: {"message": "deleted"})
    args = cli.build_parser().parse_args(["delete", "7"])
    args.func(args)
    mock_delete.assert_called_once_with(f"{cli.API_URL}/items/7")


@patch("cli.requests.get")
def test_cmd_search_external_by_barcode(mock_get):
    mock_get.return_value = Mock(json=lambda: {"name": "Item"})
    args = cli.build_parser().parse_args(["search-external", "--barcode", "123"])
    args.func(args)
    mock_get.assert_called_once_with(f"{cli.API_URL}/external/barcode/123")


@patch("cli.requests.post")
def test_cmd_import_calls_expected_endpoint(mock_post):
    mock_post.return_value = Mock(json=lambda: {"id": 1, "name": "Nutella"})
    args = cli.build_parser().parse_args(["import", "3017620422003", "--quantity", "1", "--price", "4.99"])
    args.func(args)
    mock_post.assert_called_once_with(
        f"{cli.API_URL}/items/import/3017620422003",
        json={"quantity": 1, "price": 4.99},
    )
