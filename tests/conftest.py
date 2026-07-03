import os
import sys

import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app as app_module  # noqa: E402


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True

    with app_module.app.app_context():
        app_module.db.create_all()

    with app_module.app.test_client() as test_client:
        yield test_client

    with app_module.app.app_context():
        app_module.db.session.remove()
        app_module.db.drop_all()
