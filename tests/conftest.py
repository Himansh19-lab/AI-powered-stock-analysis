import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Provide dummy test credentials so cloud SDKs can initialize without crashing on CI runners
os.environ.setdefault("AWS_ACCESS_KEY_ID", "mock_aws_access_key")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "mock_aws_secret_key")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("OPENAI_API_KEY", "mock_openai_api_key")

# Ensure src/ is on sys.path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backend.api.route import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
