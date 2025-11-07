from app.backend.db.models import QryBranchOfficesModel
from sqlalchemy import func
import json
from datetime import datetime
import pdfkit
import os

class TagClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, branch_office_id=None, page=1, items_per_page=10):
        try:
            # Query base con join a visibility_statuses para obtener el estado
            query = self.db.query(
                QryBranchOfficesModel.id,
                QryBranchOfficesModel.branch_office,
                QryBranchOfficesModel.address,
                QryBranchOfficesModel.region,
                QryBranchOfficesModel.commune,
                QryBranchOfficesModel.zone,
                QryBranchOfficesModel.segment,
                QryBranchOfficesModel.principal,
                QryBranchOfficesModel.dte_code,
                QryBranchOfficesModel.principal_supervisor,
                QryBranchOfficesModel.full_name,
                QryBranchOfficesModel.person_who_receives,
                QryBranchOfficesModel.rut_who_receives,
                QryBranchOfficesModel.phone_who_receives
            )
            
            # Filtrar por branch_office_id si se proporciona
            if branch_office_id:
                query = query.filter(QryBranchOfficesModel.id == branch_office_id)
            
            # Contar total de registros
            total_count = query.count()
            
            # Aplicar paginación
            offset = (page - 1) * items_per_page
            data = query.order_by(QryBranchOfficesModel.id.desc()).offset(offset).limit(items_per_page).all()
            
            if not data:
                return {
                    "data": [],
                    "total": 0,
                    "page": page,
                    "items_per_page": items_per_page,
                    "total_pages": 0
                }
            
            # Formatear los resultados
            result = []
            for tag in data:
                result.append({
                    "id": tag.id,
                    "branch_office": tag.branch_office,
                    "address": tag.address,
                    "region": tag.region,
                    "commune": tag.commune,
                    "zone": tag.zone,
                    "segment": tag.segment,
                    "principal": tag.principal,
                    "dte_code": tag.dte_code,
                    "principal_supervisor": tag.principal_supervisor,
                    "full_name": tag.full_name,
                    "person_who_receives": tag.person_who_receives,
                    "rut_who_receives": tag.rut_who_receives,
                    "phone_who_receives": tag.phone_who_receives
                })
            
            return {
                "data": result,
                "total": total_count,
                "page": page,
                "items_per_page": items_per_page,
                "total_pages": (total_count + items_per_page - 1) // items_per_page
            }
            
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def generate_pdf_labels(self, branch_office_id):
        try:
            # Obtener datos de la sucursal
            branch_data = self.db.query(QryBranchOfficesModel).filter(
                QryBranchOfficesModel.id == branch_office_id
            ).first()
            
            if not branch_data:
                return {"error": "Sucursal no encontrada"}
            
            # HTML template para 4 etiquetas (2x2)
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: Letter;
                        margin: 0.5cm;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: Arial, sans-serif;
                    }}
                    .container {{
                        width: 100%;
                        height: 100vh;
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: space-between;
                        align-content: space-between;
                        padding: 10px;
                        box-sizing: border-box;
                    }}
                    .label {{
                        width: 48%;
                        height: 48%;
                        border: 2px solid #000;
                        box-sizing: border-box;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        page-break-inside: avoid;
                    }}
                    .label h2 {{
                        font-size: 24px;
                        margin: 10px 0;
                        color: #333;
                    }}
                    .label h1 {{
                        font-size: 32px;
                        margin: 15px 0;
                        color: #000;
                        font-weight: bold;
                    }}
                    .label p {{
                        font-size: 18px;
                        margin: 8px 0;
                        color: #555;
                    }}
                    .label .name {{
                        font-size: 22px;
                        font-weight: bold;
                        color: #000;
                        margin: 15px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="label">
                        <h2>{branch_data.branch_office}</h2>
                        <h1>Recibe:</h1>
                        <p class="name">{branch_data.person_who_receives or 'N/A'}</p>
                        <p>RUT: {branch_data.rut_who_receives or 'N/A'}</p>
                        <p>Teléfono: {branch_data.phone_who_receives or 'N/A'}</p>
                    </div>
                    <div class="label">
                        <h2>{branch_data.branch_office}</h2>
                        <h1>Recibe:</h1>
                        <p class="name">{branch_data.person_who_receives or 'N/A'}</p>
                        <p>RUT: {branch_data.rut_who_receives or 'N/A'}</p>
                        <p>Teléfono: {branch_data.phone_who_receives or 'N/A'}</p>
                    </div>
                    <div class="label">
                        <h2>{branch_data.branch_office}</h2>
                        <h1>Recibe:</h1>
                        <p class="name">{branch_data.person_who_receives or 'N/A'}</p>
                        <p>RUT: {branch_data.rut_who_receives or 'N/A'}</p>
                        <p>Teléfono: {branch_data.phone_who_receives or 'N/A'}</p>
                    </div>
                    <div class="label">
                        <h2>{branch_data.branch_office}</h2>
                        <h1>Recibe:</h1>
                        <p class="name">{branch_data.person_who_receives or 'N/A'}</p>
                        <p>RUT: {branch_data.rut_who_receives or 'N/A'}</p>
                        <p>Teléfono: {branch_data.phone_who_receives or 'N/A'}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Configurar opciones de pdfkit
            options = {
                'page-size': 'Letter',
                'margin-top': '0.5cm',
                'margin-right': '0.5cm',
                'margin-bottom': '0.5cm',
                'margin-left': '0.5cm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"etiqueta_{branch_office_id}_{timestamp}.pdf"
            filepath = os.path.join('files', filename)
            
            # Asegurar que el directorio existe
            os.makedirs('files', exist_ok=True)
            
            # Generar PDF
            pdfkit.from_string(html_content, filepath, options=options)
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath
            }
            
        except Exception as e:
            error_message = str(e)
            return {"error": f"Error al generar PDF: {error_message}"}