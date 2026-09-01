from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CustomerModel, BranchOfficeModel, UserModel, ExpenseTypeModel
from app.backend.classes.customer_class import CustomerClass
from app.backend.classes.whatsapp_class import WhatsappClass
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.file_class import FileClass
from sqlalchemy import desc, case
from sqlalchemy.dialects import mysql
from sqlalchemy import or_
from datetime import datetime, timedelta
from fastapi import HTTPException
import requests
import json
import base64
import uuid
from sqlalchemy.sql import func


class CustomerCreditNoteClass:
    def __init__(self, db: Session):
        self.db = db
        self.file_class = FileClass(db)  # Crear una instancia de FileClass

    def get_all(self, rol_id = None, rut = None, group=1, page=0, items_per_page=10, period=None):
        try:
            if rol_id == 1 or rol_id == 2:
                # Rol 1 y 2: Ver todas las notas de crédito
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id.in_([1, 2]))
                filters.append(DteModel.dte_type_id == 61)

                # Para notas de crédito, incluir status 14 (supervisor) y status 5 (procesado)
                filters.append(or_(DteModel.status_id == 14, DteModel.status_id == 5))

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DteModel.id, 
                    DteModel.branch_office_id, 
                    DteModel.folio, 
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    DteModel.sii_status_id,
                    DteModel.sii_track_id,
                    DteModel.sii_rejection_reason,
                    DteModel.sii_status_checked_at,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).join(
                    CustomerModel, DteModel.rut == CustomerModel.rut, isouter=True
                ).join(
                    BranchOfficeModel, DteModel.branch_office_id == BranchOfficeModel.id, isouter=True
                ).filter(*filters)

            elif rol_id == 4:
                # Rol 4: Solo ver las notas de crédito de las sucursales que supervisa
                # Inicialización de filtros dinámicos
                filters = []

                filters.append(DteModel.dte_version_id.in_([1, 2]))
                filters.append(DteModel.dte_type_id == 61)  # Tipo 61 para notas de crédito
                filters.append(DteModel.rut != None)

                # Para notas de crédito, incluir status 14 (supervisor) y status 5 (procesado)
                filters.append(or_(DteModel.status_id == 14, DteModel.status_id == 5))

                # Usar el período proporcionado o el período actual
                if period:
                    filters.append(DteModel.period == period)
                else:
                    current_period = datetime.now().strftime('%Y-%m')
                    filters.append(DteModel.period == current_period)

                # Construir la consulta base con los filtros aplicados - solo sucursales que supervisa
                query = self.db.query(
                    DteModel.id, 
                    DteModel.branch_office_id, 
                    DteModel.folio, 
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    DteModel.sii_status_id,
                    DteModel.sii_track_id,
                    DteModel.sii_rejection_reason,
                    DteModel.sii_status_checked_at,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).join(
                    CustomerModel, DteModel.rut == CustomerModel.rut, isouter=True
                ).join(
                    BranchOfficeModel, DteModel.branch_office_id == BranchOfficeModel.id, isouter=True
                ).filter(
                    BranchOfficeModel.principal_supervisor == rut  # Filtrar por supervisor
                ).filter(*filters)

            else:
                # Otros roles: devolver vacío
                return {'credit_notes': [], 'total_count': 0}

            # Ordenar y paginar - primero status 14, después status 5, por ID descendente
            total_count = query.count()
            print(f"DEBUG - Total credit notes with status 14 and 5: {total_count}")
            print(f"DEBUG - Period filter: {period if period else datetime.now().strftime('%Y-%m')}")
            
            # Mostrar el SQL generado
            compiled = query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True})
            print(f"DEBUG - SQL Query: {compiled}")
            
            query = query.order_by(
                case(
                    (DteModel.status_id == 14, 1),
                    (DteModel.status_id == 5, 2),
                    else_=3
                ),
                desc(DteModel.id)
            )

            if page > 0:
                offset = (page - 1) * items_per_page
                query = query.offset(offset).limit(items_per_page)

            dtes = query.all()

            # Formatear los resultados
            result = []
            from app.backend.classes.dte_sii_status_class import serialize_dte_sii_fields

            for dte in dtes:
                result.append({
                    'id': dte.id,
                    'branch_office_id': dte.branch_office_id,
                    'folio': dte.folio,
                    'total': dte.total,
                    'added_date': dte.added_date.isoformat() if dte.added_date else None,
                    'rut': dte.rut,
                    'status_id': dte.status_id,
                    'chip_id': dte.chip_id,
                    'customer': dte.customer,
                    'branch_office': dte.branch_office,
                    **serialize_dte_sii_fields(dte),
                })

            return {
                'credit_notes': result,
                'total_count': total_count,
                'page': page,
                'items_per_page': items_per_page
            }

        except Exception as e:
            print(f"ERROR in get_all: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving credit notes: {str(e)}")

    def get_one(self, dte_id):
        try:
            # Buscar el DTE específico (puede ser factura/boleta o nota de crédito)
            dte = self.db.query(DteModel).filter(
                DteModel.id == dte_id
            ).first()

            if not dte:
                raise HTTPException(status_code=404, detail="DTE not found")

            # Si es una factura o boleta (tipo 33 o 39), verificar si ya tiene una nota de crédito
            existing_credit_note = None
            if dte.dte_type_id in [33, 39] and dte.folio and dte.folio > 0:
                existing_credit_note = self.db.query(DteModel).filter(
                    DteModel.dte_type_id == 61,  # Nota de crédito
                    DteModel.denied_folio == dte.folio,  # El folio de la factura/boleta está en denied_folio
                    DteModel.rut == dte.rut,  # Mismo RUT
                    DteModel.dte_version_id == 1
                ).first()
                
                if existing_credit_note:
                    print(f"DEBUG - Ya existe nota de crédito para folio {dte.folio}: NC ID {existing_credit_note.id}, NC folio {existing_credit_note.folio}")

            # Obtener información del cliente
            customer = self.db.query(CustomerModel).filter(CustomerModel.rut == dte.rut).first()

            # Obtener información de la sucursal
            branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == dte.branch_office_id).first()

            # Si es una nota de crédito (tipo 61), buscar el DTE original usando denied_folio
            original_dte = None
            if dte.dte_type_id == 61 and hasattr(dte, 'denied_folio') and dte.denied_folio:
                original_dte = self.db.query(DteModel).filter(
                    DteModel.folio == dte.denied_folio,
                    DteModel.dte_type_id.in_([33, 39]),  # Facturas o boletas
                    DteModel.rut == dte.rut,  # Mismo RUT
                    DteModel.dte_version_id == 1
                ).first()

            result = {
                'id': dte.id,
                'branch_office_id': dte.branch_office_id,
                'branch_office': branch_office.branch_office if branch_office else None,
                'folio': dte.folio,
                'dte_type_id': dte.dte_type_id,
                'status_id': dte.status_id,
                'rut': dte.rut,
                'customer': customer.customer if customer else None,
                'cash_amount': dte.cash_amount,
                'total': dte.total,
                'subtotal': dte.subtotal,
                'tax': dte.tax,
                'period': dte.period,
                'added_date': dte.added_date.isoformat() if dte.added_date else None,
                'comment': dte.comment,
                'reason_id': dte.reason_id,
                'denied_folio': getattr(dte, 'denied_folio', None),
                'has_credit_note': existing_credit_note is not None,
                'existing_credit_note': {
                    'id': existing_credit_note.id,
                    'folio': existing_credit_note.folio,
                    'status_id': existing_credit_note.status_id,
                    'total': existing_credit_note.total,
                    'added_date': existing_credit_note.added_date.isoformat() if existing_credit_note.added_date else None
                } if existing_credit_note else None,
                'original_dte': {
                    'id': original_dte.id,
                    'folio': original_dte.folio,
                    'dte_type_id': original_dte.dte_type_id,
                    'total': original_dte.total
                } if original_dte else None
            }

            return result

        except HTTPException:
            raise
        except Exception as e:
            print(f"ERROR in get_one: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving credit note: {str(e)}")

    def search(self, rol_id=None, rut=None, branch_office_id=None, customer_rut=None, customer=None, status_id=None, supervisor_id=None, page=0, items_per_page=10):
        try:
            if rol_id == 1 or rol_id == 2:
                filters = []
                filters.append(DteModel.dte_version_id.in_([1, 2]))
                filters.append(DteModel.dte_type_id == 61)  # Notas de crédito
                filters.append(DteModel.rut != None)

                # Aplicar filtros adicionales
                if branch_office_id:
                    filters.append(DteModel.branch_office_id == branch_office_id)
                
                if customer_rut:
                    filters.append(DteModel.rut == customer_rut)
                
                if status_id:
                    filters.append(DteModel.status_id == status_id)

                # Construir la consulta base con los filtros aplicados
                query = self.db.query(
                    DteModel.id, 
                    DteModel.branch_office_id, 
                    DteModel.folio, 
                    DteModel.total,
                    DteModel.added_date,
                    DteModel.rut,
                    DteModel.status_id,
                    DteModel.chip_id,
                    CustomerModel.customer,
                    BranchOfficeModel.branch_office
                ).join(
                    CustomerModel, DteModel.rut == CustomerModel.rut, isouter=True
                ).join(
                    BranchOfficeModel, DteModel.branch_office_id == BranchOfficeModel.id, isouter=True
                ).filter(*filters)

                # Aplicar filtro por nombre de cliente si se proporciona
                if customer:
                    query = query.filter(CustomerModel.customer.like(f'%{customer}%'))

                total_count = query.count()
                query = query.order_by(desc(DteModel.id))

                if page > 0:
                    offset = (page - 1) * items_per_page
                    query = query.offset(offset).limit(items_per_page)

                dtes = query.all()

                result = []
                for dte in dtes:
                    result.append({
                        'id': dte.id,
                        'branch_office_id': dte.branch_office_id,
                        'folio': dte.folio,
                        'total': dte.total,
                        'added_date': dte.added_date.isoformat() if dte.added_date else None,
                        'rut': dte.rut,
                        'status_id': dte.status_id,
                        'chip_id': dte.chip_id,
                        'customer': dte.customer,
                        'branch_office': dte.branch_office
                    })

                return {
                    'credit_notes': result,
                    'total_count': total_count
                }

            else:
                return {'credit_notes': [], 'total_count': 0}

        except Exception as e:
            print(f"ERROR in search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error searching credit notes: {str(e)}")

    def get(self, dte_id):
        try:
            return self.get_one(dte_id)
        except Exception as e:
            print(f"ERROR in get: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving credit note: {str(e)}")

    def download(self, dte_id):
        """
        PDF de NC emitida (tipo 61).
        Primero SimpleFactura (NC recientes / pool); si falla, LibreDTE (NC viejas).
        """
        try:
            dte = self.db.query(DteModel).filter(
                DteModel.id == dte_id,
                DteModel.dte_type_id == 61
            ).first()

            if not dte:
                return None

            if not dte.folio or int(dte.folio) == 0:
                return None

            folio = int(dte.folio)

            # 1) SimpleFactura — muchas NC con dte_version_id=1 también están ahí
            try:
                from app.backend.classes.customer_ticket_class import CustomerTicketClass

                pdf_result = CustomerTicketClass(self.db).save_simplefactura_pdf_ticket(
                    folio,
                    dte_type_id=61,
                )
                if pdf_result.get("status") == "success":
                    remote_path = f"{folio}.pdf"
                    file_contents = self.file_class.download(remote_path)
                    return {
                        "file_name": f"NC_{folio}.pdf",
                        "file_data": base64.b64encode(file_contents).decode("utf-8"),
                    }
                print(
                    f"[credit_note download] SimpleFactura folio={folio}: {pdf_result}",
                    flush=True,
                )
            except Exception as sf_exc:
                print(
                    f"[credit_note download] SimpleFactura folio={folio} error: {sf_exc}",
                    flush=True,
                )

            # 2) LibreDTE — NC históricas
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {TOKEN}",
            }
            libredte_urls = [
                (
                    f"https://libredte.cl/api/dte/dte_emitidos/pdf/61/{folio}/76063822"
                    f"?formato=general&papelContinuo=0&copias_tributarias=1"
                    f"&copias_cedibles=1&cedible=0&compress=0&base64=0"
                ),
                (
                    f"https://libredte.cl/api/dte/dte_emitidos/pdf/61/{folio}/76063822-6"
                    f"?formato=general&papelContinuo=0&copias_tributarias=1"
                    f"&copias_cedibles=1&cedible=0&compress=0&base64=0"
                ),
            ]

            response = None
            for url in libredte_urls:
                response = requests.get(url, headers=headers, timeout=60)
                if (
                    response.status_code == 200
                    and response.content
                    and response.content[:4] == b"%PDF"
                ):
                    break
                response = requests.post(
                    url,
                    headers={**headers, "Content-Type": "application/json"},
                    timeout=60,
                )
                if (
                    response.status_code == 200
                    and response.content
                    and response.content[:4] == b"%PDF"
                ):
                    break

            if (
                not response
                or response.status_code != 200
                or not response.content
                or response.content[:4] != b"%PDF"
            ):
                print(
                    f"[credit_note download] LibreDTE PDF folio={folio} "
                    f"HTTP {getattr(response, 'status_code', None)} "
                    f"{(getattr(response, 'text', None) or '')[:120]}",
                    flush=True,
                )
                return None

            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            unique_id = uuid.uuid4().hex[:8]
            unique_filename = f"NC_{folio}_{timestamp}_{unique_id}.pdf"
            self.file_class.temporal_upload(response.content, unique_filename)
            file_contents = self.file_class.download(unique_filename)
            encoded_file = base64.b64encode(file_contents).decode("utf-8")
            self.file_class.delete(unique_filename)

            return {
                "file_name": unique_filename,
                "file_data": encoded_file,
            }

        except Exception as e:
            print(f"ERROR in credit_note download: {str(e)}")
            return None

    def verify(self, dte_id):
        try:
            # Obtener la nota de crédito
            dte = self.db.query(DteModel).filter(
                DteModel.id == dte_id,
                DteModel.dte_type_id == 61
            ).first()

            if not dte:
                return "Credit note not found"

            if not dte.folio or dte.folio == 0:
                return "Credit note has no folio - cannot verify"

            # Verificar el estado en LibreDTE
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
            url = f"https://libredte.cl/api/dte/dte_emitidos/info/61/{dte.folio}/76063822"
            
            response = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {TOKEN}",
                    "Content-Type": "application/json",
                }
            )

            if response.status_code == 200:
                response_data = response.json()
                return response_data
            else:
                return f"Error verifying credit note: {response.status_code}"

        except Exception as e:
            print(f"ERROR in verify: {str(e)}")
            return f"Error verifying credit note: {str(e)}"

    def delete(self, dte_id):
        try:
            # Obtener la nota de crédito
            dte = self.db.query(DteModel).filter(
                DteModel.id == dte_id,
                DteModel.dte_type_id == 61
            ).first()

            if not dte:
                return "Credit note not found"

            # Solo permitir eliminar notas de crédito con status 14 (supervisor) o 2 (pendiente)
            if dte.status_id not in [2, 14]:
                return "Cannot delete processed credit note"

            # Eliminar la nota de crédito
            self.db.delete(dte)
            self.db.commit()

            return "Credit note deleted successfully"

        except Exception as e:
            print(f"ERROR in delete: {str(e)}")
            self.db.rollback()
            return f"Error deleting credit note: {str(e)}"

    def delete_by_denied_folio(self, denied_folio):
        """
        Delete credit notes that have the specified denied_folio
        Returns the number of deleted credit notes
        """
        try:
            # Find all credit notes with the specified denied_folio
            credit_notes = self.db.query(DteModel).filter(
                DteModel.dte_type_id == 61,
                DteModel.denied_folio == denied_folio
            ).all()

            if not credit_notes:
                return 0

            deleted_count = 0
            for dte in credit_notes:
                # Only allow deletion of credit notes with status 14 (supervisor) or 2 (pending)
                if dte.status_id in [2, 14]:
                    self.db.delete(dte)
                    deleted_count += 1
                else:
                    print(f"Skipping credit note {dte.id} with status {dte.status_id} - cannot delete processed credit note")

            self.db.commit()
            return deleted_count

        except Exception as e:
            print(f"ERROR in delete_by_denied_folio: {str(e)}")
            self.db.rollback()
            return 0

    def change_status(self, dte_id):
        try:
            # Obtener la nota de crédito
            dte = self.db.query(DteModel).filter(
                DteModel.id == dte_id,
                DteModel.dte_type_id == 61
            ).first()

            if not dte:
                return "Credit note not found"

            # Cambiar status según el estado actual
            if dte.status_id == 14:  # De supervisor a pendiente
                dte.status_id = 2
                message = "Credit note status changed to pending"
            elif dte.status_id == 2:  # De pendiente a supervisor
                dte.status_id = 14
                message = "Credit note status changed to supervisor"
            else:
                return "Cannot change status of processed credit note"

            self.db.add(dte)
            self.db.commit()

            return message

        except Exception as e:
            print(f"ERROR in change_status: {str(e)}")
            self.db.rollback()
            return f"Error changing status: {str(e)}"
