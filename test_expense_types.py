import requests
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import random

# Configuración de bases de datos para testing
DB1_URI = "mysql+pymysql://admin:Chile2025@jisbackend.com:3306/newerp"
DB2_URI = "mysql+pymysql://admin:Chile2025@jisbackend.com:3306/jisparking"

# Crear engines
engine_db1 = create_engine(DB1_URI)
engine_db2 = create_engine(DB2_URI)

# Crear sessions
SessionDB1 = sessionmaker(bind=engine_db1)
SessionDB2 = sessionmaker(bind=engine_db2)

def create_test_data():
    """Crear datos de prueba en ambas bases de datos"""
    
    # Datos aleatorios de prueba
    test_accounts = [
        "5101001", "5102001", "5103001", "5104001", "5105001",
        "6101001", "6102001", "6103001", "7101001", "7102001"
    ]
    
    # Algunos accounts que estarán en ambas bases (para probar coincidencias)
    common_accounts = ["5101001", "5102001", "5103001"]
    
    # Algunos accounts solo en DB1
    db1_only = ["5104001", "5105001"]
    
    # Algunos accounts solo en DB2
    db2_only = ["6101001", "6102001"]
    
    print("🔧 Creando datos de prueba...")
    
    # Insertar en DB1 (base principal)
    with SessionDB1() as db1:
        try:
            # Limpiar datos de prueba anteriores
            db1.execute(text("DELETE FROM expense_types WHERE accounting_account LIKE '51%' OR accounting_account LIKE '61%' OR accounting_account LIKE '71%'"))
            
            # Insertar datos en DB1
            all_db1_accounts = common_accounts + db1_only
            for i, account in enumerate(all_db1_accounts, 1):
                query = text("""
                    INSERT INTO expense_types 
                    (accounting_account, expense_type, capitulation_visibility_id, eerr_visibility_id, track_visibility_id, type, group_detail, positive_negative_id)
                    VALUES (:account, :expense_type, :cap_vis, :eerr_vis, :track_vis, :type, :group_detail, :pos_neg)
                """)
                
                db1.execute(query, {
                    "account": account,
                    "expense_type": f"Gasto Tipo {i}",
                    "cap_vis": random.randint(1, 3),
                    "eerr_vis": random.randint(1, 3),
                    "track_vis": random.randint(1, 3),
                    "type": random.randint(1, 2),
                    "group_detail": random.randint(1, 5),
                    "pos_neg": None  # Inicialmente NULL para ver el update
                })
            
            db1.commit()
            print(f"✅ Insertados {len(all_db1_accounts)} registros en DB1 (principal)")
            
        except Exception as e:
            print(f"❌ Error en DB1: {e}")
            db1.rollback()
    
    # Insertar en DB2 (base externa)
    with SessionDB2() as db2:
        try:
            # Limpiar datos de prueba anteriores
            db2.execute(text("DELETE FROM expense_types WHERE accounting_account LIKE '51%' OR accounting_account LIKE '61%' OR accounting_account LIKE '71%'"))
            
            # Insertar datos en DB2
            all_db2_accounts = common_accounts + db2_only
            for i, account in enumerate(all_db2_accounts, 1):
                query = text("""
                    INSERT INTO expense_types 
                    (accounting_account, expense_type, capitulation_visibility_id, eerr_visibility_id, track_visibility_id, type, group_detail)
                    VALUES (:account, :expense_type, :cap_vis, :eerr_vis, :track_vis, :type, :group_detail)
                """)
                
                db2.execute(query, {
                    "account": account,
                    "expense_type": f"Gasto Externo {i}",
                    "cap_vis": random.randint(1, 3),
                    "eerr_vis": random.randint(1, 3),
                    "track_vis": random.randint(1, 3),
                    "type": random.randint(10, 20),  # Valores diferentes para ver el update
                    "group_detail": random.randint(1, 5)
                })
            
            db2.commit()
            print(f"✅ Insertados {len(all_db2_accounts)} registros en DB2 (externa)")
            
        except Exception as e:
            print(f"❌ Error en DB2: {e}")
            db2.rollback()
    
    print(f"🎯 Cuentas que deberían coincidir: {common_accounts}")
    return common_accounts

def test_endpoint():
    """Probar el endpoint de comparación y update"""
    
    print("\n🚀 Probando endpoint /expense_types/external_data...")
    
    try:
        # Hacer petición al endpoint
        response = requests.get("http://localhost:8000/expense_types/external_data")
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("message", {})
            
            print("✅ Endpoint respondió correctamente")
            print(f"📊 Total de cuentas coincidentes: {result.get('total_matching_accounts', 0)}")
            print(f"📝 Cuentas coincidentes: {result.get('matching_accounts', [])}")
            print(f"🔄 Total de updates realizados: {result.get('total_updates', 0)}")
            
            # Mostrar detalles de los updates
            updates = result.get('updates_made', [])
            if updates:
                print("\n📋 Detalles de updates realizados:")
                for update in updates:
                    print(f"  - ID: {update['id']}")
                    print(f"    Cuenta: {update['accounting_account']}")
                    print(f"    Valor anterior: {update['old_positive_negative_id']}")
                    print(f"    Valor nuevo: {update['new_positive_negative_id']}")
                    print("    ---")
            else:
                print("⚠️ No se realizaron updates")
            
            return True
            
        else:
            print(f"❌ Error en endpoint: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error al probar endpoint: {e}")
        return False

def verify_updates():
    """Verificar que los updates se realizaron correctamente"""
    
    print("\n🔍 Verificando updates en la base de datos...")
    
    with SessionDB1() as db1:
        try:
            query = text("""
                SELECT accounting_account, positive_negative_id 
                FROM expense_types 
                WHERE accounting_account LIKE '51%' 
                AND positive_negative_id IS NOT NULL
                ORDER BY accounting_account
            """)
            
            result = db1.execute(query)
            updated_records = result.fetchall()
            
            if updated_records:
                print("✅ Records actualizados encontrados:")
                for record in updated_records:
                    print(f"  - Cuenta: {record.accounting_account}, positive_negative_id: {record.positive_negative_id}")
            else:
                print("⚠️ No se encontraron records actualizados")
                
        except Exception as e:
            print(f"❌ Error al verificar updates: {e}")

def cleanup_test_data():
    """Limpiar datos de prueba"""
    
    print("\n🧹 Limpiando datos de prueba...")
    
    # Limpiar DB1
    with SessionDB1() as db1:
        try:
            db1.execute(text("DELETE FROM expense_types WHERE accounting_account LIKE '51%' OR accounting_account LIKE '61%' OR accounting_account LIKE '71%'"))
            db1.commit()
            print("✅ Datos de prueba eliminados de DB1")
        except Exception as e:
            print(f"❌ Error limpiando DB1: {e}")
    
    # Limpiar DB2
    with SessionDB2() as db2:
        try:
            db2.execute(text("DELETE FROM expense_types WHERE accounting_account LIKE '51%' OR accounting_account LIKE '61%' OR accounting_account LIKE '71%'"))
            db2.commit()
            print("✅ Datos de prueba eliminados de DB2")
        except Exception as e:
            print(f"❌ Error limpiando DB2: {e}")

def main():
    """Función principal de testing"""
    
    print("🧪 INICIANDO TESTING DEL ENDPOINT EXPENSE_TYPES")
    print("=" * 50)
    
    # 1. Crear datos de prueba
    expected_matches = create_test_data()
    
    # 2. Probar el endpoint
    endpoint_success = test_endpoint()
    
    # 3. Verificar que los updates se hicieron
    if endpoint_success:
        verify_updates()
    
    # 4. Limpiar datos de prueba
    cleanup_test_data()
    
    print("\n🏁 Testing completado")

if __name__ == "__main__":
    main()
