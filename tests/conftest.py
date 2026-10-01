import os

# main.py가 import되기 전에 환경변수 세팅해야 core/security.py가 값을 읽고 API 키 목록을 구성
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["API_KEYS"] = "test-key=pytest"
os.environ["JWT_SECRET_KEY"] = "test-secret-for-pytest-only"
os.environ["DEFAULT_ADMIN_USERNAME"] = "admin"
os.environ["DEFAULT_ADMIN_PASSWORD"] = "testpassword-pytest"

import pytest
from fastapi.testclient import TestClient
from main import app

TEST_API_KEY = "test-key"
AUTH_HEADERS = {"X-API-Key": TEST_API_KEY}


# with 블록으로 감싸야 lifespan(startup/shutdown)이 실제로 실행됨
# -> seed_default_admin()이 이때 호출되어 admin 계정이 생성됨
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c