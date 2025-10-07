#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Archivo temporal para probar que las importaciones circulares se han resuelto
"""

def test_dte_imports():
    try:
        from app.backend.classes.dte_class import DteClass
        print("✓ DteClass importado correctamente")
        return True
    except ImportError as e:
        print(f"✗ Error al importar DteClass: {e}")
        return False

def test_whatsapp_imports():
    try:
        from app.backend.classes.whatsapp_class import WhatsappClass
        print("✓ WhatsappClass importado correctamente")
        return True
    except ImportError as e:
        print(f"✗ Error al importar WhatsappClass: {e}")
        return False

def test_customer_ticket_imports():
    try:
        from app.backend.classes.customer_ticket_class import CustomerTicketClass
        print("✓ CustomerTicketClass importado correctamente")
        return True
    except ImportError as e:
        print(f"✗ Error al importar CustomerTicketClass: {e}")
        return False

def test_customer_bill_imports():
    try:
        from app.backend.classes.customer_bill_class import CustomerBillClass
        print("✓ CustomerBillClass importado correctamente")
        return True
    except ImportError as e:
        print(f"✗ Error al importar CustomerBillClass: {e}")
        return False

if __name__ == "__main__":
    print("Probando importaciones...")
    print("=" * 50)
    
    results = []
    results.append(test_dte_imports())
    results.append(test_whatsapp_imports())
    results.append(test_customer_ticket_imports())
    results.append(test_customer_bill_imports())
    
    print("=" * 50)
    successful = sum(results)
    total = len(results)
    
    if all(results):
        print(f"🎉 Todas las importaciones exitosas ({successful}/{total})")
        print("Las importaciones circulares se han resuelto correctamente!")
    else:
        print(f"⚠️  {successful}/{total} importaciones exitosas")
        print("Aún hay problemas de importación circular pendientes")
