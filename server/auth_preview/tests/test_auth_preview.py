"""Auth preview tests: isolated temporary SQLite database, no original app changes."""
import pytest
from fastapi.testclient import TestClient
from auth_preview.app import build_app


@pytest.fixture
def client(tmp_path):
    application = build_app(
        db_url=f'sqlite:///{(tmp_path / "users.sqlite3").as_posix()}',
        jwt_secret='test-only-32-character-key-never-use-in-prod',
    )
    with TestClient(application) as test_client:
        yield test_client


def test_register_login_me(client):
    registered = client.post('/api/auth/register', json={
        'name': 'Tester', 'email': 'Demo@Example.com', 'password': 'safe_password_123'
    })
    assert registered.status_code == 201
    assert registered.json()['email'] == 'demo@example.com'
    assert 'password' not in registered.json()
    duplicate = client.post('/api/auth/register', json={
        'name': 'Tester', 'email': 'demo@example.com', 'password': 'safe_password_123'
    })
    assert duplicate.status_code == 409
    assert client.get('/api/users/me').status_code == 401
    assert client.post('/api/auth/login', json={
        'email': 'demo@example.com', 'password': 'wrong_password'
    }).status_code == 401
    login = client.post('/api/auth/login', json={
        'email': 'demo@example.com', 'password': 'safe_password_123'
    })
    assert login.status_code == 200
    token = login.json()['access_token']
    profile = client.get('/api/users/me', headers={'Authorization': f'Bearer {token}'})
    assert profile.status_code == 200
    assert profile.json()['name'] == 'Tester'
    assert client.get('/api/users/me', headers={'Authorization': 'Bearer invalid'}).status_code == 401


def test_validation(client):
    assert client.post('/api/auth/register', json={
        'name': 'A', 'email': 'invalid', 'password': 'abc'
    }).status_code == 422
