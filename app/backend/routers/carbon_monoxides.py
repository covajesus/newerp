from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.backend.db.database import get_db
from app.backend.classes.carbon_monoxide_class import CarbonMonoxideClass
from app.backend.classes.email_class import EmailClass
from app.backend.classes.file_class import FileClass
from app.backend.schemas import CarbonMonoxideList, CarbonMonoxide, ReportRequest
from sqlalchemy.orm import Session
from datetime import datetime
import base64
import json
import uuid

carbon_monoxides = APIRouter(
    prefix="/carbon_monoxides",
    tags=["CarbonMonoxides"]
)

@carbon_monoxides.post("/")
def index(carbon_monoxide: CarbonMonoxideList, db: Session = Depends(get_db)):
    carbon_monoxide_data = CarbonMonoxideClass(db).get_all(carbon_monoxide.branch_office_id, carbon_monoxide.since_date, carbon_monoxide.until_date, carbon_monoxide.page)

    return {"message": carbon_monoxide_data}

@carbon_monoxides.post("/store")
def store(
    form_data: CarbonMonoxide = Depends(CarbonMonoxide.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]  # 8 caracteres únicos
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'carbon_monoxide'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)

        CarbonMonoxideClass(db).store(form_data, remote_path)

        return {"message": message}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")
    
@carbon_monoxides.delete("/delete/{id}")
def delete(id:int, db: Session = Depends(get_db)):
    patent_data = CarbonMonoxideClass(db).get(id)

    patent_data = json.loads(patent_data)

    file_name = patent_data["carbon_monoxide_data"]["support"]

    remote_path = f"{file_name}"

    message = FileClass(db).delete(remote_path)

    if message == "success":
        CarbonMonoxideClass(db).delete(id)

    return {"message": message}

@carbon_monoxides.get("/download/{id}")
def download(id: int, db: Session = Depends(get_db)):
    carbon_monoxide_data = CarbonMonoxideClass(db).get(id)

    carbon_monoxide_data = json.loads(carbon_monoxide_data)
    file_name = carbon_monoxide_data["carbon_monoxide_data"]["support"]

    remote_path = f"{file_name}"

    file_contents = FileClass(db).download(remote_path)

    encoded_file = base64.b64encode(file_contents).decode('utf-8')

    return {
        "file_name": file_name,
        "file_data": encoded_file
    }
    
@carbon_monoxides.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    try:
        # Obtener los datos del contrato
        patent_data = CarbonMonoxideClass(db).get(id)
        
        # Verificar si se encontró el contrato
        if not patent_data:
            raise HTTPException(status_code=404, detail="Patente no encontrada")

        # Si el contrato se encuentra, devolver los datos
        return {"message": patent_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el iva: {str(e)}")

@carbon_monoxides.post("/send_report")
def send_report(request: ReportRequest, db: Session = Depends(get_db)):
    print(request.selected_carbon_monoxides)

    email_content = "<h2>Reporte de Monóxido de Carbono</h2>"

    for item in request.selected_carbon_monoxides:
        carbon_monoxide = CarbonMonoxideClass(db).get(item["id"])
        data = json.loads(carbon_monoxide)

        carbon_data = data["carbon_monoxide_data"]
        file_support = FileClass(db).get(carbon_data["support"])

        if file_support:
            email_content += f'<img src="{file_support}" height="400" /><br>'

        email_content += "<ul>"
        email_content += "<li>Sucursal: " + str(carbon_data["branch_office"]) + ". Fecha de Registro: " + str(carbon_data["added_date"]) + ", Medición: " + str(carbon_data["measure_value"]) + ".</li>"
        email_content += "</ul>"

    email_client = EmailClass("informacion@jisparking.com", "pksh nfit pcwj dfte")

    result = email_client.send_email(request.email, "Informe de Monóxido de Carbono", email_content)

    return {"message": result}
