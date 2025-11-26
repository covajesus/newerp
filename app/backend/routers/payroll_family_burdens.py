from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin, UploadFamilyBurden
from app.backend.classes.payroll_item_value_class import PayrollItemValueClass
from app.backend.classes.payroll_family_burden_class import PayrollFamilyBurdenClass
from app.backend.auth.auth_user import get_current_active_user
from fastapi import UploadFile, File, HTTPException
import pandas as pd
import io

payroll_family_burdens = APIRouter(
    prefix="/payroll_family_burdens",
    tags=["PayrollFamilyBurdens"]
)

@payroll_family_burdens.get("/{section_id}/{period}")
def index(section_id:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollFamilyBurdenClass(db).get(section_id, period)

    return {"message": data}

@payroll_family_burdens.get("/edit/{rut}/{item_id}/{period}")
def edit(rut:int, item_id:int, period:str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollItemValueClass(db).get_with_period(rut, item_id, period)

    return {"message": data}

@payroll_family_burdens.post("/upload")
async def upload(form_data: UploadFamilyBurden = Depends(UploadFamilyBurden.as_form), file: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        file_content = await file.read()
        file_bytesio = io.BytesIO(file_content)
        df = pd.read_excel(file_bytesio, engine='openpyxl', usecols=['Rut', 'Tramo', 'N° Cargas', 'Monto Familiar', 'Monto Retroactivo'])
        payroll_manual_input_data = df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo: {str(e)}")
    
    for payroll_manual_input in payroll_manual_input_data:
        family_burdens = {}

        for key, value in payroll_manual_input.items():
            if key == 'Rut':
                family_burdens['rut'] = value
            elif key == 'Tramo':
                family_burdens['section'] = value
            elif key == 'N° Cargas':
                family_burdens['burden'] = value
            elif key == 'Monto Familiar':
                family_burdens['family_amount'] = value
            elif key == 'Monto Retroactivo':
                family_burdens['retroactive_amount'] = value

        PayrollFamilyBurdenClass(db).multiple_store(form_data, family_burdens)

    return 1