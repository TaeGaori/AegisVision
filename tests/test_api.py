from tests.conftest import AUTH_HEADERS


# ---공개 엔드포인트(/health)---

def test_health_is_public_and_ok(client):
    """인증 없어도 /health는 200을 반환"""
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "model_loaded" in body


# ---인증---

def test_metrics_requires_api_key(client):
    """인증 없이 /metrics를 호출하면 401을 반환"""
    response = client.get("/metrics")
    assert response.status_code == 401

def test_metrics_rejects_invalid_key(client):
    """잘못된 API키는 401을 반환"""
    response = client.get("/metrics", headers={"X-API-Key": "wrongkey"})
    assert response.status_code == 401

def test_metrics_accepts_valid_key(client):
    """올바른 API키는 200과 지표 필드들이 반환"""
    response = client.get("/metrics", headers=AUTH_HEADERS)
    assert response.status_code == 200
    body = response.json()
    assert "total_requests" in body
    assert "avg_confidence" in body

def test_model_info_requires_api_key(client):
    response = client.get("/model/info")
    assert response.status_code == 401

def test_training_history_requires_api_key(client):
    response = client.get("/model/training-history")
    assert response.status_code == 401


# ---/predict - 입력 검증---

def test_predict_without_file_returns_422(client):
    """파일 없이 /predict를 호출하면 요청 검증 단계에서 422가 반환"""
    response = client.post("/predict", headers=AUTH_HEADERS)
    assert response.status_code == 422

def test_predict_without_api_key_returns_401(client):
    """인증 없이는 파일을 보내도 먼저 401이 반환"""
    fake_file = {"file": ("test.jpg", b"not a real image", "image/jpeg")}
    response = client.post("/predict", files=fake_file)
    assert response.status_code == 401

# ---/auth/login---

def test_login_with_wrong_password_fails(client):
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "wrong-password"}
    )
    assert response.status_code in (400, 401)

def test_login_with_correct_password_returns_token(client):
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "testpassword-pytest"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()