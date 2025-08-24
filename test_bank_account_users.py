import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Simulación de login (ajusta el endpoint y payload según tu sistema)
def get_auth_headers():
    response = client.post("/login", json={"email": "admin@admin.com", "password": "admin"})
    assert response.status_code == 200
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def test_create_and_get_bank_account_user():
    headers = get_auth_headers()
    # Crear cuenta bancaria
    payload = {
        "bank_account_name": "Mi Cuenta",
        "bank_account_type_id": 1,
        "bank_account_number": 12345678,
        "bank_account_email": "cuenta@banco.com"
    }
    response = client.post("/bank_account_users/store", json=payload, headers=headers)
    assert response.status_code == 200
    assert "success" in response.text

    # Obtener cuentas bancarias del usuario autenticado
    response = client.get("/bank_account_users/", headers=headers)
    assert response.status_code == 200
    assert "bank_account_name" in response.text
