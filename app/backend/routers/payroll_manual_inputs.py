from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import UserLogin
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import PayrollDataInput, UploadPayrollManualInput
from app.backend.classes.payroll_manual_input_class import PayrollManualInputClass
import pandas as pd
import io

payroll_manual_inputs = APIRouter(
    prefix="/payroll_manual_inputs",
    tags=["PayrollManualInput"]
)

@payroll_manual_inputs.post("/store")
def store(payroll_manual_inputs: PayrollDataInput, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = PayrollManualInputClass(db).store(payroll_manual_inputs)

    return {"message": data}

@payroll_manual_inputs.post("/upload")
async def upload(form_data: UploadPayrollManualInput = Depends(UploadPayrollManualInput.as_form), file: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        file_content = await file.read()
        file_bytesio = io.BytesIO(file_content)
        df = pd.read_excel(file_bytesio, engine='openpyxl', usecols=['Rut', 'Monto'])
        payroll_manual_input_data = df.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo: {str(e)}")

    for payroll_manual_input in payroll_manual_input_data:
        
        for key, value in payroll_manual_input.items():
            if key == 'Rut':
                form_data.rut = value
            if key == 'Monto':
                form_data.amount = value

        PayrollManualInputClass(db).multiple_store(form_data)

    return 1
