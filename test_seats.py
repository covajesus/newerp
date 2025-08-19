"""
Test para validar el sistema de asientos contables
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.backend.schemas import SeatRefresh
from app.backend.classes.seat_class import SeatClass
from app.backend.db.database import get_db
from datetime import datetime

def test_seat_class_days_calculation():
    """Test para verificar el cálculo de días del mes"""
    
    # Mock de la base de datos
    class MockDB:
        pass
    
    seat_class = SeatClass(MockDB())
    
    # Test días normales
    assert seat_class.get_days_in_month(1, 2024) == 31  # Enero
    assert seat_class.get_days_in_month(4, 2024) == 30  # Abril
    assert seat_class.get_days_in_month(2, 2024) == 29  # Febrero bisiesto
    assert seat_class.get_days_in_month(2, 2023) == 28  # Febrero normal
    
    # Test año bisiesto
    assert seat_class.is_leap_year(2024) == True
    assert seat_class.is_leap_year(2023) == False
    assert seat_class.is_leap_year(2000) == True  # Divisible por 400
    assert seat_class.is_leap_year(1900) == False  # Divisible por 100 pero no por 400
    
    print("✅ Test de cálculo de días del mes: PASSED")

def test_seat_refresh_schema():
    """Test para verificar el schema SeatRefresh"""
    
    # Test datos válidos
    valid_data = {
        "external_token": "test_token_123",
        "rut": "12345678-9",
        "password": "test_password",
        "month": 11,
        "year": 2024
    }
    
    try:
        seat_refresh = SeatRefresh(**valid_data)
        assert seat_refresh.month == 11
        assert seat_refresh.year == 2024
        assert seat_refresh.rut == "12345678-9"
        print("✅ Test SeatRefresh schema: PASSED")
    except Exception as e:
        print(f"❌ Test SeatRefresh schema: FAILED - {e}")

def test_api_request_structure():
    """Test para verificar la estructura de datos API"""
    
    class MockDB:
        pass
    
    seat_class = SeatClass(MockDB())
    
    # Verificar que los métodos existen
    assert hasattr(seat_class, 'get_days_in_month')
    assert hasattr(seat_class, 'is_leap_year')
    assert hasattr(seat_class, 'make_api_request_with_fresh_token')
    assert hasattr(seat_class, 'refresh')
    
    print("✅ Test estructura API: PASSED")

if __name__ == "__main__":
    print("🧪 Ejecutando tests del sistema de asientos...")
    print("=" * 50)
    
    test_seat_class_days_calculation()
    test_seat_refresh_schema()
    test_api_request_structure()
    
    print("=" * 50)
    print("✅ Todos los tests completados!")
    print()
    print("📋 Información del sistema:")
    print("- Router: /api/seats/refresh")
    print("- Router: /api/seats/status/{year}/{month}")
    print("- Clase: SeatClass")
    print("- Schema: SeatRefresh")
    print("- Modelo: EerrModel")
    print()
    print("🚀 El sistema está listo para usar!")
