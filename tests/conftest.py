import os
import tempfile

# Must run before any app import: settings are read at import time.
_tmpdir = tempfile.mkdtemp(prefix="scoutbridge-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["CHPP_MOCK"] = "1"
os.environ["SECRET_KEY"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


def login(client, ht_user_id):
    r = client.post("/auth/mock", data={"ht_user_id": ht_user_id}, follow_redirects=True)
    assert r.status_code == 200
    return r
