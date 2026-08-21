from app.backend.db.models import HonoraryModel, EmployeeModel, EmployeeLaborDatumModel, UserModel, BranchOfficeModel, SupervisorModel, BankModel, RegionModel, CommuneModel, HonoraryReasonModel
from sqlalchemy import desc
from datetime import datetime, date
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.commune_class import CommuneClass
from app.backend.classes.region_class import RegionClass
from app.backend.classes.helper_class import HelperClass
import unicodedata
from sqlalchemy import func
from app.backend.classes.accounting_entry_class import AccountingEntryClass

class HonoraryClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, search_branch_office_id=None, search_rut=None, rut=None, rol_id=None, page=1, items_per_page=10):

        try:
            filters = []
            # branch_office_id = 0 se usa en frontend como "sin filtro"
            if search_branch_office_id not in (None, 0, '0', ''):
                filters.append(HonoraryModel.branch_office_id == search_branch_office_id)

            if search_rut is not None and search_rut != '':
                normalized_search_rut = (
                    str(search_rut).strip().replace('.', '').replace('-', '').upper()
                )
                filters.append(
                    func.upper(
                        func.replace(
                            func.replace(HonoraryModel.replacement_employee_rut, '.', ''),
                            '-',
                            ''
                        )
                    ) == normalized_search_rut
                )

            print(rol_id)

            if rol_id == 1 or rol_id == 2 or rol_id == 5:
                data_query = self.db.query(HonoraryModel.status_id, HonoraryModel.id, UserModel.full_name, HonoraryReasonModel.honorary_reason, HonoraryModel.replacement_employee_rut, HonoraryModel.replacement_employee_full_name, HonoraryModel.period, HonoraryModel.added_date). \
                    outerjoin(BranchOfficeModel, BranchOfficeModel.id == HonoraryModel.branch_office_id). \
                    outerjoin(HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id). \
                    outerjoin(UserModel, UserModel.rut == HonoraryModel.requested_by). \
                    filter(
                        *filters
                    ).order_by(HonoraryModel.id.desc())
                
                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                if not data:
                    return "No data found"

                serialized_data = [{
                    "status_id": honorary.status_id,
                    "id": honorary.id,
                    "requested_by": honorary.full_name,
                    "honorary_reason": honorary.honorary_reason,
                    "replacement_employee_rut": honorary.replacement_employee_rut,
                    "replacement_employee_full_name": honorary.replacement_employee_full_name,
                    "period": honorary.period,
                    "added_date": honorary.added_date
                } for honorary in data]

            else:
                data_query = self.db.query(HonoraryModel.status_id, HonoraryModel.id, UserModel.full_name, HonoraryReasonModel.honorary_reason, HonoraryModel.replacement_employee_rut, HonoraryModel.replacement_employee_full_name, HonoraryModel.period, HonoraryModel.added_date). \
                    outerjoin(BranchOfficeModel, BranchOfficeModel.id == HonoraryModel.branch_office_id). \
                    outerjoin(HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id). \
                    outerjoin(UserModel, UserModel.rut == HonoraryModel.requested_by). \
                    filter(HonoraryModel.requested_by == rut). \
                    filter(
                        *filters
                    ).order_by(HonoraryModel.id.desc())

                data = data_query.offset((page - 1) * items_per_page).limit(items_per_page).all()
                total_items = data_query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return "Invalid page number"

                if not data:
                    return "No data found"

                # Serializar los datos
                serialized_data = [{
                    "status_id": honorary.status_id,
                    "id": honorary.id,
                    "requested_by": honorary.full_name,
                    "honorary_reason": honorary.honorary_reason,
                    "replacement_employee_rut": honorary.replacement_employee_rut,
                    "replacement_employee_full_name": honorary.replacement_employee_full_name,
                    "period": honorary.period,
                    "added_date": honorary.added_date
                } for honorary in data]

            return {
                "total_items": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "items_per_page": items_per_page,
                "data": serialized_data
            }

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    
    def get(self, field, value):
        try:
            data = self.db.query(HonoraryModel).filter(getattr(HonoraryModel, field) == value).first()

            serialized_data = {
                "honorary_reason_id": data.honorary_reason_id,
                "branch_office_id": data.branch_office_id,
                "foreigner_id": data.foreigner_id,
                "bank_id": data.bank_id,
                "account_type_id": data.account_type_id,
                "schedule_id": data.schedule_id,
                "region_id": data.region_id,
                "commune_id": data.commune_id,
                "requested_by": data.requested_by,
                "status_id": data.status_id,
                "employee_to_replace": str(data.employee_to_replace),
                "replacement_employee_rut": str(data.replacement_employee_rut),
                "replacement_employee_full_name": data.replacement_employee_full_name,
                "address": str(data.address),
                "account_number": str(data.account_number),
                "start_date": str(data.start_date),
                "end_date": str(data.end_date),
                "amount": str(data.amount),
                "observation": str(data.observation),
            }

            return json.dumps(serialized_data)

        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, requested_by, honorary_inputs):
        try:
            honorary = HonoraryModel()
            honorary.honorary_reason_id = honorary_inputs.honorary_reason_id
            honorary.branch_office_id = honorary_inputs.branch_office_id
            honorary.foreigner_id = honorary_inputs.foreigner_id
            honorary.bank_id = honorary_inputs.bank_id
            honorary.schedule_id = honorary_inputs.schedule_id
            honorary.region_id = honorary_inputs.region_id
            honorary.commune_id = honorary_inputs.commune_id
            honorary.account_type_id = honorary_inputs.account_type_id
            honorary.requested_by = requested_by
            honorary.status_id = 14
            honorary.employee_to_replace = honorary_inputs.employee_to_replace
            honorary.replacement_employee_rut = honorary_inputs.replacement_employee_rut
            honorary.replacement_employee_full_name = honorary_inputs.replacement_employee_full_name
            honorary.email = honorary_inputs.email
            honorary.address = honorary_inputs.address
            honorary.account_number = honorary_inputs.account_number
            if honorary_inputs.start_date != 'None' and honorary_inputs.start_date != None:
                honorary.start_date = honorary_inputs.start_date
            if honorary_inputs.end_date != 'None' and honorary_inputs.end_date != None:
                honorary.end_date = honorary_inputs.end_date
            honorary.observation = honorary_inputs.observation
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def generate(self, id, honorary_inputs):
        try:
            honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
            honorary.honorary_reason_id = honorary_inputs.honorary_reason_id
            honorary.branch_office_id = honorary_inputs.branch_office_id
            honorary.foreigner_id = honorary_inputs.foreigner_id
            honorary.bank_id = honorary_inputs.bank_id
            honorary.schedule_id = honorary_inputs.schedule_id
            honorary.region_id = honorary_inputs.region_id
            honorary.commune_id = honorary_inputs.commune_id
            honorary.account_type_id = honorary_inputs.account_type_id
            honorary.status_id = 2
            honorary.employee_to_replace = honorary_inputs.employee_to_replace
            honorary.replacement_employee_rut = honorary_inputs.replacement_employee_rut
            honorary.replacement_employee_full_name = honorary_inputs.replacement_employee_full_name
            honorary.email = honorary_inputs.email
            honorary.address = honorary_inputs.address
            honorary.account_number = honorary_inputs.account_number
            if honorary_inputs.start_date != 'None' and honorary_inputs.start_date != None:
                honorary.start_date = honorary_inputs.start_date
            if honorary_inputs.end_date != 'None' and honorary_inputs.end_date != None:
                honorary.end_date = honorary_inputs.end_date
            honorary.observation = honorary_inputs.observation
            honorary.amount = honorary_inputs.amount
            honorary.added_date = datetime.now()
            honorary.updated_date = datetime.now()

            self.db.add(honorary)
            self.db.commit()

            if honorary_inputs.foreigner_id == 1:
                self.send(honorary)

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def validate(self, data):
        data = self.db.query(HonoraryModel).filter(HonoraryModel.replacement_employee_rut == data.replacement_employee_rut).filter(func.date(HonoraryModel.added_date) == str(data.added_date)[:10]).count()
            
        return data
    
    def impute(self, form_data):
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"

        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == form_data.id).first()
        settings = SettingClass(self.db).get()
        
        american_date = form_data.period + '-01'
        utf8_date = HelperClass.convert_to_utf8(american_date)
        expense_type = '443000344'
        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.id == honorary.branch_office_id
        ).first()

        gloss = (
                branch_office.branch_office
                + "_"
                + expense_type
                + "_"
                + utf8_date
                + "_Honorario_"
                + str(form_data.id)
            )
        gross_amount = HelperClass().remove_from_string('.', str(honorary.amount))
        gross_amount = round(int(gross_amount) / float(settings["setting_data"]["percentage_honorary_bill"]))
        tax = int(gross_amount) - int(honorary.amount)
        net_amount = round(gross_amount - tax)
        
        data = {
                "fecha": american_date,
                "glosa": gloss,
                "detalle": {
                    "debe": {
                        111000102: gross_amount
                    },
                    "haber": {
                        expense_type: net_amount,
                        "221000223": tax,
                    }
                },
                "operacion": "I",
                "documentos": {
                    "emitidos": [
                        {
                            "dte": '',
                            "folio": '',
                        }
                    ]
                },
            }

        result = AccountingEntryClass(self.db).create(data, token=TOKEN)

        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == form_data.id).first()
        honorary.status_id = 15
        honorary.period = form_data.period
        honorary.updated_date = datetime.now()

        self.db.add(honorary)
        self.db.commit()

        return "Accounting entry created successfully"

    def massive_accountability(self):
        """
        Crea asientos contables masivos para todos los honorarios con status_id = 2.
        Recorre toda la tabla honoraries y genera un asiento contable para cada uno,
        similar al método impute pero procesando todos los registros de una vez.
        """
        TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
        
        # Buscar todos los honorarios con status_id = 2
        honoraries = self.db.query(HonoraryModel).filter(HonoraryModel.status_id == 2).all()
        
        if not honoraries:
            return {
                "status": "success",
                "message": "No se encontraron honorarios con status_id = 2 para procesar",
                "processed": 0,
                "errors": []
            }
        
        settings = SettingClass(self.db).get()
        processed = 0
        errors = []
        
        for honorary in honoraries:
            try:
                # Usar el periodo fijo 2025-12 para todos los honorarios
                period = "2025-12"
                american_date = period + '-01'
                utf8_date = HelperClass.convert_to_utf8(american_date)
                expense_type = '443000344'
                
                branch_office = self.db.query(BranchOfficeModel).filter(
                    BranchOfficeModel.id == honorary.branch_office_id
                ).first()
                
                if not branch_office:
                    errors.append({
                        "honorary_id": honorary.id,
                        "error": "No se encontró la sucursal asociada"
                    })
                    continue
                
                gloss = (
                    branch_office.branch_office
                    + "_"
                    + expense_type
                    + "_"
                    + utf8_date
                    + "_Honorario_"
                    + str(honorary.id)
                )
                
                gross_amount = HelperClass().remove_from_string('.', str(honorary.amount))
                gross_amount = round(int(gross_amount) / float(settings["setting_data"]["percentage_honorary_bill"]))
                tax = int(gross_amount) - int(honorary.amount)
                net_amount = round(gross_amount - tax)
                
                data = {
                    "fecha": american_date,
                    "glosa": gloss,
                    "detalle": {
                        "debe": {
                            111000102: gross_amount
                        },
                        "haber": {
                            expense_type: net_amount,
                            "221000223": tax,
                        }
                    },
                    "operacion": "I",
                    "documentos": {
                        "emitidos": [
                            {
                                "dte": '',
                                "folio": '',
                            }
                        ]
                    },
                }
                
                result = AccountingEntryClass(self.db).create(data, token=TOKEN)
                
                # Verificar si la respuesta fue exitosa
                if result.get("status") not in ("success", "partial"):
                    errors.append({
                        "honorary_id": honorary.id,
                        "error": f"Error al crear asiento contable: {result.get('status')} - {result.get('errors') or result}"
                    })
                    continue
                
                # Actualizar el honorario: status_id = 15 y period = "2025-12"
                honorary.status_id = 15
                honorary.period = "2025-12"
                honorary.updated_date = datetime.now()
                
                self.db.add(honorary)
                processed += 1
                
            except Exception as e:
                errors.append({
                    "honorary_id": honorary.id,
                    "error": f"Error al procesar honorario: {str(e)}"
                })
                continue
        
        # Hacer commit de todos los cambios
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"Error al guardar cambios en la base de datos: {str(e)}",
                "processed": processed,
                "errors": errors
            }
        
        return {
            "status": "success",
            "message": f"Procesamiento masivo completado. {processed} honorarios procesados exitosamente.",
            "processed": processed,
            "total_found": len(honoraries),
            "errors": errors
        }
        
    @staticmethod
    def _normalize_commune_name(name: str) -> str:
        text = unicodedata.normalize("NFKD", (name or "").strip().upper())
        text = "".join(c for c in text if not unicodedata.combining(c))
        return " ".join(text.replace("-", " ").split())

    def _resolve_sii_region_comuna(self, region_id, commune_id) -> tuple[int, int, str]:
        """Map IntraJIS region/commune to SII BTE codes."""
        from app.backend.classes.sii.bte_communes import REGIONS

        region = RegionClass(self.db).get("id", region_id)
        commune = CommuneClass(self.db).get("id", commune_id)
        if not region or isinstance(region, str):
            raise ValueError("Región no encontrada")
        if not commune or isinstance(commune, str):
            raise ValueError("Comuna no encontrada")

        sii_region = int(
            getattr(region, "simplefactura_region_code", None)
            or getattr(region, "region_remuneration_code", None)
            or 0
        )
        if sii_region not in REGIONS:
            # Fallback: try IntraJIS id if it matches SII catalog
            sii_region = int(getattr(region, "id", 0) or 0)
        if sii_region not in REGIONS:
            raise ValueError(
                f"No se pudo mapear región IntraJIS id={region_id} a código SII BTE"
            )

        commune_name = getattr(commune, "commune", None) or ""
        target = self._normalize_commune_name(commune_name)
        comuna_code = None
        for cid, cname in REGIONS[sii_region].items():
            if self._normalize_commune_name(cname) == target:
                comuna_code = int(cid)
                break
        if comuna_code is None:
            # Partial match (e.g. SAN PEDRO DE MELIPILLA vs SAN PEDRO)
            for cid, cname in REGIONS[sii_region].items():
                n = self._normalize_commune_name(cname)
                if target and (target in n or n in target):
                    comuna_code = int(cid)
                    break
        if comuna_code is None:
            raise ValueError(
                f"No se pudo mapear comuna '{commune_name}' a código SII (región {sii_region})"
            )
        return sii_region, comuna_code, commune_name

    def send(self, data):
        """Emite BTE ante el SII (Clave Tributaria) — reemplaza SimpleFactura BHE terceros."""
        try:
            from app.backend.classes.sii.bte import emit_bte
        except ModuleNotFoundError as e:
            print(f"Missing dependency for SII BTE: {e}")
            return {
                "status": "error",
                "message": f"Falta dependencia para BTE SII: {e}. Instale httpx en el venv del servicio.",
            }

        settings = SettingClass(self.db).get()
        creds = SettingClass(self.db).get_sii_credentials()
        login_rut = creds.get("login_rut") or ""
        password = creds.get("password") or ""
        if not login_rut or not password:
            print("Clave Tributaria SII no configurada; no se emite BTE")
            return {
                "status": "error",
                "message": "Configure RUT y Clave Tributaria SII en Configuraciones",
            }

        pct = settings.get("setting_data", {}).get("percentage_honorary_bill") or "1"
        amount_raw = HelperClass().remove_from_string(".", str(data.amount))
        try:
            amount = round(int(amount_raw) / float(pct))
        except (TypeError, ValueError, ZeroDivisionError):
            amount = int(amount_raw or 0)

        try:
            sii_region, sii_comuna, _commune_name = self._resolve_sii_region_comuna(
                data.region_id, data.commune_id
            )
        except Exception as e:
            print(f"Error mapeo región/comuna SII: {e}")
            return {"status": "error", "message": str(e)}

        beneficiary_rut = str(getattr(data, "replacement_employee_rut", "") or "").strip()
        beneficiary_name = (
            getattr(data, "replacement_employee_full_name", None) or "Beneficiario"
        ).strip()
        domicilio = (getattr(data, "address", None) or "Sin dirección").strip()
        servicio = f"Boleta de Honorarios para {beneficiary_name}"

        try:
            result = emit_bte(
                login_rut=login_rut,
                password=password,
                beneficiary_rut=beneficiary_rut,
                beneficiary_name=beneficiary_name,
                domicilio=domicilio,
                region=sii_region,
                comuna=sii_comuna,
                servicio=servicio,
                monto=int(amount),
                issue_date=date.today(),
            )
            print(
                f"BTE emitida SII folio={result.folio} bruto={result.monto_bruto} "
                f"ret={result.retencion} liq={result.liquido}"
            )
            # Guardar folio en observation si hay registro con id
            honorary_id = getattr(data, "id", None)
            if honorary_id:
                row = (
                    self.db.query(HonoraryModel)
                    .filter(HonoraryModel.id == honorary_id)
                    .first()
                )
                if row:
                    note = f"BTE SII folio {result.folio}"
                    prev = (row.observation or "").strip()
                    row.observation = f"{prev} | {note}".strip(" |") if prev else note
                    row.updated_date = datetime.now()
                    self.db.commit()
            return {
                "status": "success",
                "message": "Boleta de honorarios (BTE) emitida en SII",
                "folio": result.folio,
                "monto_bruto": result.monto_bruto,
                "retencion": result.retencion,
                "liquido": result.liquido,
            }
        except Exception as e:
            print(f"Error al emitir BTE en SII: {e}")
            return {"status": "error", "message": str(e)}

    def get_data_by_rut(self, rut):
        """
        Busca si el usuario con el RUT dado tiene boletas de honorarios 
        y devuelve la más próxima (próxima fecha de inicio)
        """
        try:
            # Buscar honorarios para el RUT dado que estén activos y con fecha futura
            current_date = datetime.now().date()
            
            honorary = self.db.query(
                HonoraryModel.id,
                HonoraryModel.honorary_reason_id,
                HonoraryModel.branch_office_id,
                HonoraryModel.foreigner_id,
                HonoraryModel.bank_id,
                HonoraryModel.schedule_id,
                HonoraryModel.region_id,
                HonoraryModel.commune_id,
                HonoraryModel.account_type_id,
                HonoraryModel.requested_by,
                HonoraryModel.status_id,
                HonoraryModel.employee_to_replace,
                HonoraryModel.replacement_employee_rut,
                HonoraryModel.address,
                HonoraryModel.account_number,
                HonoraryModel.start_date,
                HonoraryModel.end_date,
                HonoraryModel.email,
                HonoraryModel.amount,
                HonoraryModel.observation,
                HonoraryModel.replacement_employee_full_name,
                HonoraryReasonModel.honorary_reason,
            ).outerjoin(
                HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id
            ).filter(
                HonoraryModel.replacement_employee_rut == rut,
                HonoraryModel.start_date >= current_date,  # Solo fechas futuras o actuales
                HonoraryModel.status_id.in_([1, 2, 3])  # Estados activos (ajustar según tu lógica)
            ).order_by(
                HonoraryModel.start_date.asc()  # La más próxima primero
            ).first()

            if honorary:
                return {
                    "status": "found",
                    "data": {
                        "id": honorary.id,
                        "honorary_reason_id": honorary.honorary_reason_id,
                        "branch_office_id": honorary.branch_office_id,
                        "foreigner_id": honorary.foreigner_id,
                        "bank_id": honorary.bank_id,
                        "schedule_id": honorary.schedule_id,
                        "region_id": honorary.region_id,
                        "commune_id": honorary.commune_id,
                        "account_type_id": honorary.account_type_id,
                        "requested_by": honorary.requested_by,
                        "replacement_employee_rut": honorary.replacement_employee_rut,
                        "replacement_employee_full_name": honorary.replacement_employee_full_name,
                        "address": honorary.address,
                        "account_number": honorary.account_number,
                        "start_date": honorary.start_date.strftime("%Y-%m-%d") if honorary.start_date else None,
                        "end_date": honorary.end_date.strftime("%Y-%m-%d") if honorary.end_date else None,
                        "email": honorary.email,
                        "amount": honorary.amount,
                        "status_id": honorary.status_id,
                        "observation": honorary.observation,
                        "honorary_reason": honorary.honorary_reason
                    }
                }
            else:
                # Si no encontró honorarios futuros, buscar el más reciente
                last_honorary = self.db.query(
                    HonoraryModel.id,
                    HonoraryModel.honorary_reason_id,
                    HonoraryModel.branch_office_id,
                    HonoraryModel.foreigner_id,
                    HonoraryModel.bank_id,
                    HonoraryModel.schedule_id,
                    HonoraryModel.region_id,
                    HonoraryModel.commune_id,
                    HonoraryModel.account_type_id,
                    HonoraryModel.requested_by,
                    HonoraryModel.status_id,
                    HonoraryModel.employee_to_replace,
                    HonoraryModel.replacement_employee_rut,
                    HonoraryModel.address,
                    HonoraryModel.account_number,
                    HonoraryModel.start_date,
                    HonoraryModel.end_date,
                    HonoraryModel.email,
                    HonoraryModel.amount,
                    HonoraryModel.observation,
                    HonoraryModel.replacement_employee_full_name,
                    HonoraryReasonModel.honorary_reason,
                ).outerjoin(
                    HonoraryReasonModel, HonoraryReasonModel.id == HonoraryModel.honorary_reason_id
                ).filter(
                    HonoraryModel.replacement_employee_rut == rut
                ).order_by(
                    HonoraryModel.start_date.desc()  # El más reciente primero
                ).first()

                if last_honorary:
                    return {
                        "status": "found_past",
                        "data": {
                            "id": last_honorary.id,
                            "honorary_reason_id": last_honorary.honorary_reason_id,
                            "branch_office_id": last_honorary.branch_office_id,
                            "foreigner_id": last_honorary.foreigner_id,
                            "bank_id": last_honorary.bank_id,
                            "schedule_id": last_honorary.schedule_id,
                            "region_id": last_honorary.region_id,
                            "commune_id": last_honorary.commune_id,
                            "account_type_id": last_honorary.account_type_id,
                            "requested_by": last_honorary.requested_by,
                            "replacement_employee_rut": last_honorary.replacement_employee_rut,
                            "replacement_employee_full_name": last_honorary.replacement_employee_full_name,
                            "address": last_honorary.address,
                            "account_number": last_honorary.account_number,
                            "start_date": last_honorary.start_date.strftime("%Y-%m-%d") if last_honorary.start_date else None,
                            "end_date": last_honorary.end_date.strftime("%Y-%m-%d") if last_honorary.end_date else None,
                            "email": last_honorary.email,
                            "amount": last_honorary.amount,
                            "status_id": last_honorary.status_id,
                            "observation": last_honorary.observation,
                            "honorary_reason": last_honorary.honorary_reason
                        }
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": "No se encontraron boletas de honorarios para este RUT"
                    }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error al buscar honorarios: {str(e)}"
            }