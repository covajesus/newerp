from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import (
    PreventiveMaintenanceModel,
    PreventiveMaintenanceSectionModel,
    PreventiveMaintenanceItemModel,
    PreventiveMaintenanceResponseModel,
    BranchOfficeModel
)
from fastapi import HTTPException
from typing import List, Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import base64

class PreventiveMaintenanceClass:
    def __init__(self, db: Session):
        self.db = db

    # ========== PREVENTIVE MAINTENANCE METHODS ==========
    
    def create_preventive_maintenance(self, data: dict):
        """Crear un nuevo mantenimiento preventivo con sus respuestas"""
        try:
            # Validar que la sucursal existe
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == data['branch_office_id']
            ).first()
            
            if not branch_office:
                raise HTTPException(status_code=404, detail="Sucursal no encontrada")
            
            # Convertir maintenance_date de string a date
            maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
            
            # Crear el mantenimiento preventivo
            preventive_maintenance = PreventiveMaintenanceModel(
                branch_office_id=data['branch_office_id'],
                address=data.get('address'),
                maintenance_date=maintenance_date,
                technician_name=data['technician_name'],
                manager_name=data['manager_name'],
                detected_failures=data.get('detected_failures'),
                corrective_actions=data.get('corrective_actions'),
                technician_signature=data.get('technician_signature'),
                manager_signature=data.get('manager_signature')
            )
            
            self.db.add(preventive_maintenance)
            self.db.flush()  # Para obtener el ID
            
            # Transformar el formato del frontend (section1, section2, etc.) al formato esperado
            responses = []
            
            # Debug: ver todas las claves en data
            print(f"DEBUG create_preventive_maintenance: claves en data: {list(data.keys())}")
            
            # Obtener todos los items para mapear item_key a item_id
            all_items = self.db.query(PreventiveMaintenanceItemModel).filter(
                PreventiveMaintenanceItemModel.is_active == True
            ).all()
            item_key_to_id = {item.item_key: item.id for item in all_items}
            print(f"DEBUG create_preventive_maintenance: items encontrados: {len(item_key_to_id)}")
            
            # Procesar cada sección (section1, section2, etc.)
            for key, value in data.items():
                if key.startswith('section') and isinstance(value, dict):
                    print(f"DEBUG create_preventive_maintenance: procesando {key}")
                    section_data = value
                    observations = section_data.get('observations', {})
                    
                    # Procesar cada item en la sección
                    for item_key, response_value in section_data.items():
                        if item_key == 'observations':
                            continue
                        
                        # Obtener el item_id desde el item_key
                        item_id = item_key_to_id.get(item_key)
                        if not item_id:
                            print(f"DEBUG: Item con key '{item_key}' no encontrado en la base de datos")
                            continue
                        
                        # Obtener la observación si existe
                        observation = observations.get(item_key)
                        
                        # Agregar a las respuestas
                        responses.append({
                            'item_id': item_id,
                            'response_value': response_value,
                            'observation': observation if observation else None
                        })
                        print(f"DEBUG: Respuesta agregada - item_key: {item_key}, item_id: {item_id}, response_value: {response_value}, observation: {observation}")
            
            # Si también viene en formato responses (por compatibilidad)
            if 'responses' in data and isinstance(data['responses'], list) and len(data['responses']) > 0:
                responses = data['responses']
            
            # Debug: ver qué se está recibiendo
            print(f"DEBUG create_preventive_maintenance: responses procesadas: {len(responses)}")
            
            # Verificar que hay respuestas
            if not responses:
                # Si no hay respuestas, hacer commit del mantenimiento sin respuestas
                self.db.commit()
                self.db.refresh(preventive_maintenance)
                return preventive_maintenance
            
            # Procesar cada respuesta
            for response_data in responses:
                try:
                    # Validar que response_data es un diccionario
                    if not isinstance(response_data, dict):
                        continue
                    
                    # Obtener item_id
                    item_id = response_data.get('item_id')
                    if not item_id:
                        continue
                    
                    # Validar que el item existe
                    item = self.db.query(PreventiveMaintenanceItemModel).filter(
                        PreventiveMaintenanceItemModel.id == item_id
                    ).first()
                    
                    if not item:
                        # Continuar con el siguiente en lugar de hacer rollback
                        continue
                    
                    # Obtener response_value y observation
                    response_value = response_data.get('response_value')
                    observation = response_data.get('observation')
                    
                    # Validar response_value si está presente
                    if response_value is not None:
                        try:
                            response_value = int(response_value)
                            if response_value not in [1, 2, 3]:
                                response_value = None
                        except (ValueError, TypeError):
                            response_value = None
                    
                    # Crear la respuesta
                    response = PreventiveMaintenanceResponseModel(
                        preventive_maintenance_id=preventive_maintenance.id,
                        item_id=item_id,
                        response_value=response_value,
                        observation=observation if observation else None
                    )
                    self.db.add(response)
                    print(f"DEBUG: Respuesta agregada - item_id: {item_id}, response_value: {response_value}, observation: {observation}")
                    
                except Exception as e:
                    # Continuar con el siguiente si hay error en una respuesta
                    print(f"Error al crear respuesta: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            # Hacer commit de todo
            try:
                self.db.commit()
                self.db.refresh(preventive_maintenance)
            except Exception as e:
                self.db.rollback()
                raise HTTPException(status_code=500, detail=f"Error al guardar respuestas: {str(e)}")
            
            return preventive_maintenance
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear mantenimiento preventivo: {str(e)}")
    
    def get_preventive_maintenance(self, maintenance_id: int):
        """Obtener un mantenimiento preventivo por ID con sus respuestas"""
        try:
            maintenance = self.db.query(PreventiveMaintenanceModel).filter(
                PreventiveMaintenanceModel.id == maintenance_id
            ).first()
            
            if not maintenance:
                raise HTTPException(status_code=404, detail="Mantenimiento preventivo no encontrado")
            
            return maintenance
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener mantenimiento preventivo: {str(e)}")
    
    def get_all_preventive_maintenances(self, branch_office_id: Optional[int] = None, page: int = 1, items_per_page: int = 10):
        """Obtener todos los mantenimientos preventivos con paginación"""
        try:
            # Construir la consulta con join a BranchOfficeModel para obtener el nombre
            query = self.db.query(
                PreventiveMaintenanceModel.id,
                PreventiveMaintenanceModel.branch_office_id,
                PreventiveMaintenanceModel.address,
                PreventiveMaintenanceModel.maintenance_date,
                PreventiveMaintenanceModel.technician_name,
                PreventiveMaintenanceModel.manager_name,
                PreventiveMaintenanceModel.detected_failures,
                PreventiveMaintenanceModel.corrective_actions,
                PreventiveMaintenanceModel.technician_signature,
                PreventiveMaintenanceModel.manager_signature,
                PreventiveMaintenanceModel.created_at,
                PreventiveMaintenanceModel.updated_at,
                BranchOfficeModel.branch_office
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == PreventiveMaintenanceModel.branch_office_id
            )
            
            if branch_office_id:
                query = query.filter(PreventiveMaintenanceModel.branch_office_id == branch_office_id)
            
            total_items = query.count()
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            if page < 1 or (total_pages > 0 and page > total_pages):
                raise HTTPException(status_code=400, detail="Número de página inválido")
            
            results = query.order_by(PreventiveMaintenanceModel.maintenance_date.desc()).offset(
                (page - 1) * items_per_page
            ).limit(items_per_page).all()
            
            # Construir la lista de datos con el nombre de la sucursal
            data = []
            for result in results:
                data.append({
                    "id": result.id,
                    "branch_office_id": result.branch_office_id,
                    "branch_office": result.branch_office,
                    "address": result.address,
                    "maintenance_date": result.maintenance_date.strftime('%Y-%m-%d') if result.maintenance_date else None,
                    "technician_name": result.technician_name,
                    "manager_name": result.manager_name,
                    "detected_failures": result.detected_failures,
                    "corrective_actions": result.corrective_actions,
                    "technician_signature": result.technician_signature,
                    "manager_signature": result.manager_signature,
                    "created_at": result.created_at,
                    "updated_at": result.updated_at
                })
            
            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener mantenimientos preventivos: {str(e)}")
    
    def update_preventive_maintenance(self, maintenance_id: int, data: dict):
        """Actualizar un mantenimiento preventivo"""
        try:
            maintenance = self.db.query(PreventiveMaintenanceModel).filter(
                PreventiveMaintenanceModel.id == maintenance_id
            ).first()
            
            if not maintenance:
                raise HTTPException(status_code=404, detail="Mantenimiento preventivo no encontrado")
            
            # Actualizar campos
            if 'branch_office_id' in data:
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == data['branch_office_id']
                ).first()
                if not branch_office:
                    raise HTTPException(status_code=404, detail="Sucursal no encontrada")
                maintenance.branch_office_id = data['branch_office_id']
            
            if 'address' in data:
                maintenance.address = data['address']
            
            if 'maintenance_date' in data:
                maintenance.maintenance_date = datetime.strptime(data['maintenance_date'], '%Y-%m-%d').date()
            
            if 'technician_name' in data:
                maintenance.technician_name = data['technician_name']
            
            if 'manager_name' in data:
                maintenance.manager_name = data['manager_name']
            
            if 'detected_failures' in data:
                maintenance.detected_failures = data['detected_failures']
            
            if 'corrective_actions' in data:
                maintenance.corrective_actions = data['corrective_actions']
            
            if 'technician_signature' in data:
                maintenance.technician_signature = data['technician_signature']
            
            if 'manager_signature' in data:
                maintenance.manager_signature = data['manager_signature']
            
            # Actualizar respuestas si se proporcionan
            if 'responses' in data and data['responses']:
                # Eliminar respuestas existentes
                self.db.query(PreventiveMaintenanceResponseModel).filter(
                    PreventiveMaintenanceResponseModel.preventive_maintenance_id == maintenance_id
                ).delete()
                
                # Crear nuevas respuestas
                for response_data in data['responses']:
                    item = self.db.query(PreventiveMaintenanceItemModel).filter(
                        PreventiveMaintenanceItemModel.id == response_data['item_id']
                    ).first()
                    
                    if not item:
                        self.db.rollback()
                        raise HTTPException(
                            status_code=404,
                            detail=f"Item con ID {response_data['item_id']} no encontrado"
                        )
                    
                    response_value = response_data.get('response_value')
                    if response_value is not None and response_value not in [1, 2, 3]:
                        self.db.rollback()
                        raise HTTPException(
                            status_code=400,
                            detail="response_value debe ser 1 (Sí), 2 (No), o 3 (N/A)"
                        )
                    
                    response = PreventiveMaintenanceResponseModel(
                        preventive_maintenance_id=maintenance_id,
                        item_id=response_data['item_id'],
                        response_value=response_value,
                        observation=response_data.get('observation')
                    )
                    self.db.add(response)
            
            maintenance.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(maintenance)
            
            return maintenance
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar mantenimiento preventivo: {str(e)}")
    
    def delete_preventive_maintenance(self, maintenance_id: int):
        """Eliminar un mantenimiento preventivo (cascade elimina las respuestas)"""
        try:
            maintenance = self.db.query(PreventiveMaintenanceModel).filter(
                PreventiveMaintenanceModel.id == maintenance_id
            ).first()
            
            if not maintenance:
                raise HTTPException(status_code=404, detail="Mantenimiento preventivo no encontrado")
            
            self.db.delete(maintenance)
            self.db.commit()
            
            return {"message": "Mantenimiento preventivo eliminado exitosamente"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al eliminar mantenimiento preventivo: {str(e)}")
    
    # ========== SECTION METHODS ==========
    
    def get_all_sections(self, is_active: Optional[bool] = None):
        """Obtener todas las secciones"""
        try:
            query = self.db.query(PreventiveMaintenanceSectionModel)
            
            if is_active is not None:
                query = query.filter(PreventiveMaintenanceSectionModel.is_active == is_active)
            
            return query.order_by(PreventiveMaintenanceSectionModel.section_number).all()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener secciones: {str(e)}")
    
    def get_section(self, section_id: int):
        """Obtener una sección por ID"""
        try:
            section = self.db.query(PreventiveMaintenanceSectionModel).filter(
                PreventiveMaintenanceSectionModel.id == section_id
            ).first()
            
            if not section:
                raise HTTPException(status_code=404, detail="Sección no encontrada")
            
            return section
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener sección: {str(e)}")
    
    # ========== ITEM METHODS ==========
    
    def get_items_by_section(self, section_id: int, is_active: Optional[bool] = None):
        """Obtener todos los items de una sección"""
        try:
            query = self.db.query(PreventiveMaintenanceItemModel).filter(
                PreventiveMaintenanceItemModel.section_id == section_id
            )
            
            if is_active is not None:
                query = query.filter(PreventiveMaintenanceItemModel.is_active == is_active)
            
            return query.order_by(PreventiveMaintenanceItemModel.item_order).all()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener items: {str(e)}")
    
    def get_all_items(self, is_active: Optional[bool] = None):
        """Obtener todos los items agrupados por sección"""
        try:
            query = self.db.query(PreventiveMaintenanceItemModel)
            
            if is_active is not None:
                query = query.filter(PreventiveMaintenanceItemModel.is_active == is_active)
            
            items = query.order_by(
                PreventiveMaintenanceItemModel.section_id,
                PreventiveMaintenanceItemModel.item_order
            ).all()
            
            return items
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener items: {str(e)}")
    
    def get_item(self, item_id: int):
        """Obtener un item por ID"""
        try:
            item = self.db.query(PreventiveMaintenanceItemModel).filter(
                PreventiveMaintenanceItemModel.id == item_id
            ).first()
            
            if not item:
                raise HTTPException(status_code=404, detail="Item no encontrado")
            
            return item
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener item: {str(e)}")
    
    # ========== RESPONSE METHODS ==========
    
    def get_responses_by_maintenance(self, maintenance_id: int):
        """Obtener todas las respuestas de un mantenimiento preventivo"""
        try:
            responses = self.db.query(PreventiveMaintenanceResponseModel).filter(
                PreventiveMaintenanceResponseModel.preventive_maintenance_id == maintenance_id
            ).all()
            
            return responses
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener respuestas: {str(e)}")
    
    def get_maintenance_with_responses(self, maintenance_id: int):
        """Obtener un mantenimiento preventivo con todas sus respuestas y detalles de items"""
        try:
            maintenance = self.get_preventive_maintenance(maintenance_id)
            responses = self.get_responses_by_maintenance(maintenance_id)
            
            # Obtener detalles de items para cada respuesta
            response_details = []
            for response in responses:
                item = self.get_item(response.item_id)
                response_details.append({
                    "id": response.id,
                    "item_id": response.item_id,
                    "item_key": item.item_key,
                    "item_name": item.item_name,
                    "section_id": item.section_id,
                    "response_value": response.response_value,
                    "observation": response.observation,
                    "created_at": response.created_at,
                    "updated_at": response.updated_at
                })
            
            return {
                "maintenance": maintenance,
                "responses": response_details
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener mantenimiento con respuestas: {str(e)}")
    
    def generate_pdf(self, maintenance_id: int):
        """Generar PDF del mantenimiento preventivo"""
        try:
            # Obtener datos completos del mantenimiento
            maintenance = self.get_preventive_maintenance(maintenance_id)
            branch_office = self.db.query(BranchOfficeModel).filter(
                BranchOfficeModel.id == maintenance.branch_office_id
            ).first()
            
            # Obtener todas las secciones con sus items
            sections = self.get_all_sections(is_active=True)
            
            # Obtener respuestas directamente desde la base de datos
            # Hacer refresh de la sesión para asegurar que tenemos los datos más recientes
            self.db.refresh(maintenance)
            
            responses_query = self.db.query(PreventiveMaintenanceResponseModel).filter(
                PreventiveMaintenanceResponseModel.preventive_maintenance_id == maintenance_id
            ).all()
            
            # Crear diccionario con item_id como clave
            responses_dict = {}
            for r in responses_query:
                # Hacer refresh de cada respuesta para asegurar que tenemos los datos
                self.db.refresh(r)
                if r.item_id:
                    responses_dict[r.item_id] = r
            
            # Crear buffer para el PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=12,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=8,
                spaceBefore=12
            )
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            
            # Logo y Título
            try:
                # Descargar logo desde la URL
                import urllib.request
                logo_url = "https://intrajis.com/assets/logo-1jO0MaUN.png"
                logo_response = urllib.request.urlopen(logo_url)
                logo_data = logo_response.read()
                # Hacer el logo cuadrado (mismo ancho y alto)
                logo_size = 1.5*inch
                logo_img = Image(BytesIO(logo_data), width=logo_size, height=logo_size)
                
                # Crear tabla para logo y título
                header_data = [[logo_img, Paragraph("MANTENCIÓN PREVENTIVA", title_style)]]
                header_table = Table(header_data, colWidths=[1.8*inch, 4.2*inch])
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(header_table)
            except Exception as e:
                # Si falla la descarga del logo, solo mostrar el título
                print(f"Error al cargar logo: {str(e)}")
                story.append(Paragraph("MANTENCIÓN PREVENTIVA", title_style))
            
            story.append(Spacer(1, 0.2*inch))
            
            # Información general
            info_data = [
                ['Sucursal:', branch_office.branch_office if branch_office else 'N/A'],
                ['Dirección:', maintenance.address or 'N/A'],
                ['Fecha de Mantención:', maintenance.maintenance_date.strftime('%d/%m/%Y') if maintenance.maintenance_date else 'N/A'],
                ['Técnico:', maintenance.technician_name],
                ['Encargado:', maintenance.manager_name]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Secciones e items
            for section in sections:
                # Título de sección
                story.append(Paragraph(f"{section.section_number}. {section.section_name_es}", heading_style))
                
                # Obtener items de esta sección
                items = self.get_items_by_section(section.id, is_active=True)
                
                if items:
                    # Crear tabla de items
                    table_data = [['Item', 'Estado', 'Observación']]
                    
                    for item in items:
                        response = responses_dict.get(item.id)
                        status = "-"
                        observation = "-"
                        
                        if response:
                            # Obtener response_value directamente del objeto
                            response_value = response.response_value
                            
                            # Convertir response_value a texto
                            if response_value is not None:
                                try:
                                    if response_value == 1 or response_value == "1":
                                        status = "Sí"
                                    elif response_value == 2 or response_value == "2":
                                        status = "No"
                                    elif response_value == 3 or response_value == "3":
                                        status = "N/A"
                                except:
                                    pass
                            
                            # Obtener observación directamente del objeto
                            if response.observation:
                                observation = str(response.observation).strip()
                                if not observation:
                                    observation = "-"
                        
                        table_data.append([
                            item.item_name,
                            status,
                            observation
                        ])
                    
                    # Crear tabla
                    item_table = Table(table_data, colWidths=[3*inch, 1*inch, 2.5*inch])
                    item_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                        ('TOPPADDING', (0, 0), (-1, 0), 10),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                        ('TOPPADDING', (0, 1), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                    ]))
                    story.append(item_table)
                    story.append(Spacer(1, 0.2*inch))
            
            # Fallas detectadas y acciones correctivas
            if maintenance.detected_failures or maintenance.corrective_actions:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("FALLAS DETECTADAS Y ACCIONES CORRECTIVAS", heading_style))
                
                if maintenance.detected_failures:
                    story.append(Paragraph("<b>Fallas Detectadas:</b>", normal_style))
                    story.append(Paragraph(maintenance.detected_failures, normal_style))
                    story.append(Spacer(1, 0.1*inch))
                
                if maintenance.corrective_actions:
                    story.append(Paragraph("<b>Acciones Correctivas:</b>", normal_style))
                    story.append(Paragraph(maintenance.corrective_actions, normal_style))
                    story.append(Spacer(1, 0.2*inch))
            
            # Firmas
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("FIRMAS", heading_style))
            
            # Crear tabla para firmas
            signature_data = []
            
            # Firma del técnico
            tech_signature_row = ['Técnico:', '']
            if maintenance.technician_signature:
                try:
                    # Decodificar imagen base64
                    signature_data_b64 = maintenance.technician_signature
                    if signature_data_b64.startswith('data:image'):
                        signature_data_b64 = signature_data_b64.split(',')[1]
                    
                    signature_img_data = base64.b64decode(signature_data_b64)
                    signature_img = Image(BytesIO(signature_img_data), width=2*inch, height=0.8*inch)
                    tech_signature_row[1] = signature_img
                except Exception as e:
                    tech_signature_row[1] = Paragraph(maintenance.technician_name, normal_style)
            else:
                tech_signature_row[1] = Paragraph(maintenance.technician_name, normal_style)
            
            signature_data.append(tech_signature_row)
            
            # Firma del encargado
            manager_signature_row = ['Encargado:', '']
            if maintenance.manager_signature:
                try:
                    # Decodificar imagen base64
                    signature_data_b64 = maintenance.manager_signature
                    if signature_data_b64.startswith('data:image'):
                        signature_data_b64 = signature_data_b64.split(',')[1]
                    
                    signature_img_data = base64.b64decode(signature_data_b64)
                    signature_img = Image(BytesIO(signature_img_data), width=2*inch, height=0.8*inch)
                    manager_signature_row[1] = signature_img
                except Exception as e:
                    manager_signature_row[1] = Paragraph(maintenance.manager_name, normal_style)
            else:
                manager_signature_row[1] = Paragraph(maintenance.manager_name, normal_style)
            
            signature_data.append(manager_signature_row)
            
            signature_table = Table(signature_data, colWidths=[1.5*inch, 4.5*inch])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (0, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(signature_table)
            
            # Construir PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")