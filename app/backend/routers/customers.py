from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Customer, UpdateCustomer, UserLogin, CustomerList
from app.backend.classes.customer_class import CustomerClass
from app.backend.db.models import CustomerModel, Customer2Model
from app.backend.auth.auth_user import get_current_active_user
import pymysql

customers = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

@customers.post("/")
def index(customer: CustomerList, db: Session = Depends(get_db)):

    data = CustomerClass(db).get_all(customer.rut, customer.page)

    return {"message": data}

@customers.post("/store")
def store(customer_inputs:Customer, db: Session = Depends(get_db)):
    data = CustomerClass(db).store(customer_inputs)

    return {"message": data}

@customers.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = CustomerClass(db).get(id)

    return {"message": data}

@customers.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    data = CustomerClass(db).delete(id)

    return {"message": data}

@customers.post("/update/{id}")
def update(id: int, customer: UpdateCustomer, db: Session = Depends(get_db)):
    data = CustomerClass(db).update(id, customer)

    return {"message": data}

@customers.get("/existence/{rut}")
def edit(rut: str, db: Session = Depends(get_db)):
    data = CustomerClass(db).check_existence(rut)

    return {"message": data}

@customers.get("/insert_customers")
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
               customers.*,
                users.names
            FROM customers LEFT JOIN users ON customers.rut = users.rut
        """)
        result = cursor.fetchall()

        for row in result:
            rut = row['rut']
            email = row['email']
            phone = row['phone']
            region_id = row['region_id']
            commune_id = row['commune_id']
            names = row['names']
            activity = row['activity']
            address = row['address']
            print(rut, email, phone, region_id, commune_id, names, activity, address)

            customer = db.query(CustomerModel).filter(CustomerModel.rut == rut).count()
            if customer == 0:
                new_customer = Customer2Model(
                    rut=rut,
                    email=email,
                    phone=phone,
                    region_id=region_id,
                    commune_id=commune_id,
                    customer=names.upper(),
                    activity=activity,
                    address=address
                )
                db.add(new_customer)
                db.commit()
                print('Cliente guardado:', rut)
            else:
                print('El cliente ya existe:', rut)

    conn.close()

    return {"data": result}

@customers.get("/old_customers")
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
               customers.*,
                users.names
            FROM customers LEFT JOIN users ON customers.rut = users.rut
        """)
        result = cursor.fetchall()

        for row in result:
            rut = row['rut']
            email = row['email']
            phone = row['phone']
            region_id = row['region_id']
            commune_id = row['commune_id']
            names = row['names']
            activity = row['activity']
            address = row['address']
            print(rut, email, phone, region_id, commune_id, names, activity, address)

            customer = db.query(CustomerModel).filter(CustomerModel.rut == rut).count()
            if customer == 0:
                new_customer = Customer2Model(
                    rut=rut,
                    email=email,
                    phone=phone,
                    region_id=region_id,
                    commune_id=commune_id,
                    customer=names.upper(),
                    activity=activity,
                    address=address
                )
                db.add(new_customer)
                db.commit()
                print('Cliente guardado:', rut)
            else:
                print('El cliente ya existe:', rut)

    conn.close()

    return {"data": result}