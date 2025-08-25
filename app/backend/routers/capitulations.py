from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.classes.capitulation_class import CapitulationClass
from app.backend.schemas import Capitulation, CapitulationList, UpdateCapitulation, PayCapitulation, ImputeCapitulation
from app.backend.db.models import CapitulationModel
from fastapi import UploadFile, File, HTTPException
from datetime import datetime
import uuid
import json
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin
import pymysql

capitulations = APIRouter(
    prefix="/capitulations",
    tags=["Capitulations"]
)

@capitulations.post("/")
def index(capitulation: CapitulationList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CapitulationClass(db).get_all(
        session_user.rol_id, 
        session_user.rut, 
        capitulation.page,
        items_per_page=10,
        branch_office_id=capitulation.branch_office_id,
        status_id=capitulation.status_id
    )
    return {"message": data}

@capitulations.post("/search")
def search(capitulation: CapitulationList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = CapitulationClass(db).get_all(
        session_user.rol_id, 
        session_user.rut, 
        capitulation.page,
        items_per_page=10,
        branch_office_id=capitulation.branch_office_id,
        status_id=capitulation.status_id
    )
    return {"message": data}

@capitulations.post("/store")
def store(
    form_data: Capitulation = Depends(Capitulation.as_form),
    support: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'capitulation'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        CapitulationClass(db).store(form_data, session_user, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@capitulations.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    capitulation_data = CapitulationClass(db).get(id)

    capitulation_data = json.loads(capitulation_data)

    file_name = capitulation_data["capitulation_data"]["support"]

    remote_path = f"{file_name}"

    message = FileClass(db).delete(remote_path)

    if message == "success":
        CapitulationClass(db).delete(id)

    return {"message": message}
    
@capitulations.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        capitulation_data = CapitulationClass(db).get(id)

        if not capitulation_data:
            raise HTTPException(status_code=404, detail="Rendición no encontrada")

        return {"message": capitulation_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la rendición: {str(e)}")

@capitulations.post("/update")
def update(
    form_data: UpdateCapitulation = Depends(UpdateCapitulation.as_form),
    db: Session = Depends(get_db)
):
    try:
        CapitulationClass(db).update(form_data)

        return {"message": "Rendición actualizada exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la rendición: {str(e)}")

@capitulations.post("/impute")
def impute(
    form_data: ImputeCapitulation = Depends(ImputeCapitulation.as_form),
    db: Session = Depends(get_db)
):
    try:
        response = CapitulationClass(db).impute(form_data)
        print(response)

        return {"message": "Rendición imputada exitosamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la rendición: {str(e)}")

@capitulations.get("/pay/details/{rut}")
def pay_detail(
    rut: str,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        message = CapitulationClass(db).get_all_accepted(rut)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@capitulations.post("/pay")
def pay(
    form_data: PayCapitulation = Depends(PayCapitulation.as_form),
    support: UploadFile = File(None),
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        for selected_capitulation in form_data.selected_capitulations:
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
            file_category_name = 'pay_capitulation'
            unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

            remote_path = f"{file_category_name}_{unique_filename}"

            message = FileClass(db).upload(support, remote_path)

            CapitulationClass(db).pay(selected_capitulation, form_data, remote_path)

        return {"message": 'Pagado con éxito'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@capitulations.get("/support/{id}")
def support(id: int, db: Session = Depends(get_db)):

    capitulation = CapitulationClass(db).get(id)
    print(capitulation)

    capitulation_data = json.loads(capitulation)
    remote_path = capitulation_data["capitulation_data"]["support"]

    file = FileClass(db).get(remote_path)

    return {"message": file}

@capitulations.get("/payment_support/{id}")
def payment_support(id: int, db: Session = Depends(get_db)):

    capitulation = CapitulationClass(db).get(id)

    capitulation_data = json.loads(capitulation)
    remote_path = capitulation_data["capitulation_data"]["payment_support"]

    file = FileClass(db).get(remote_path)

    return {"message": file}

@capitulations.get("/total_accepted_capitulations")
def total_accepted_capitulations(rut: str = None, db: Session = Depends(get_db)):
    capitulations = CapitulationClass(db).total_accepted_capitulations(rut=rut)

    return {"message": capitulations}

@capitulations.get("/old_capitulations")
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
                *
            FROM capitulations
        """)
        result = cursor.fetchall()

        for row in result:
            print(row)
            if row['status_id'] == 7:
                status_id = 2
            
            if row['status_id'] == 11:
                status_id = 1

            if row['status_id'] == 17:
                status_id = 15

            capitulation = CapitulationModel(
                    document_type_id=row['dte_type_id'],
                    capitulation_type_id=row['capitulation_type_id'],
                    branch_office_id=row['branch_office_id'],
                    expense_type_id=row['expense_type_id'],
                    status_id=status_id,
                    document_date=row['document_date'],
                    document_number=row['document_number'],
                    user_rut=row['rut'],
                    supplier_rut=row['supplier_rut'],
                    description=row['description'],
                    amount=row['amount'],
                    support=row['support'],
                    why_was_rejected=row['why_was_rejected'],
                    payment_date=row['payment_date'],
                    payment_number=row['document_number'],
                    period=row['impute_period'],
                    added_date=row['created_at'],
                )
            db.add(capitulation)
            db.commit()