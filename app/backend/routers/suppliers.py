from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.db.models import SupplierModel, Supplier2Model
import pymysql

suppliers = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"]
)

@suppliers.get("/old_suppliers")
def old_dtes(db: Session = Depends(get_db)):
    conn = pymysql.connect(
        host='jisparking.com',
        user='jysparki_admin',
        password='Admin2024$',
        db='jysparki_jis',
        cursorclass=pymysql.cursors.DictCursor
    )

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
               supplier_data.*,
                users.names
            FROM supplier_data LEFT JOIN users ON supplier_data.rut = users.rut
        """)
        result = cursor.fetchall()

        for row in result:
            rut = row['rut']
            names = row['names']
            print(rut, names)

            supplier = db.query(SupplierModel).filter(SupplierModel.rut == rut).count()
            if supplier == 0:
                new_supplier = Supplier2Model(
                    rut=rut,
                    supplier=names
                )
                db.add(new_supplier)
                db.commit()
                print('Provedor guardado:', rut)
            else:
                print('El proveedor ya existe:', rut)

    conn.close()

    return {"data": result}