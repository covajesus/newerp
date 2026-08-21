from app.backend.db.models import HonoraryModel, EmployeeModel, EmployeeLaborDatumModel, UserModel, BranchOfficeModel, SupervisorModel, BankModel, RegionModel, CommuneModel, HonoraryReasonModel
from sqlalchemy import desc
from datetime import datetime, date
from app.backend.classes.setting_class import SettingClass
from app.backend.classes.commune_class import CommuneClass
from app.backend.classes.region_class import RegionClass
from app.backend.classes.helper_class import HelperClass
import json
import re
import unicodedata
from sqlalchemy import func
from app.backend.classes.accounting_entry_class import AccountingEntryClass

# Nunca emitir BTE al SII para estos RUT (aunque marquen "Tiene RUT = Sí").
_BTE_SII_BLOCKED_RUTS = frozenset({"271413998"})


def _normalize_rut_digits(rut) -> str:
    return re.sub(r"[^0-9Kk]", "", str(rut or "")).upper()


class HonoraryClass:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def is_bte_sii_blocked_rut(rut) -> bool:
        return _normalize_rut_digits(rut) in _BTE_SII_BLOCKED_RUTS

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
                data_query = self.db.query(
                    HonoraryModel.status_id,
                    HonoraryModel.id,
                    UserModel.full_name,
                    HonoraryReasonModel.honorary_reason,
                    HonoraryModel.replacement_employee_rut,
                    HonoraryModel.replacement_employee_full_name,
                    HonoraryModel.period,
                    HonoraryModel.added_date,
                    HonoraryModel.bte_emitted,
                    HonoraryModel.bte_folio,
                ). \
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
                    "added_date": honorary.added_date,
                    "bte_emitted": int(getattr(honorary, "bte_emitted", 0) or 0),
                    "bte_folio": getattr(honorary, "bte_folio", None),
                } for honorary in data]

            else:
                data_query = self.db.query(
                    HonoraryModel.status_id,
                    HonoraryModel.id,
                    UserModel.full_name,
                    HonoraryReasonModel.honorary_reason,
                    HonoraryModel.replacement_employee_rut,
                    HonoraryModel.replacement_employee_full_name,
                    HonoraryModel.period,
                    HonoraryModel.added_date,
                    HonoraryModel.bte_emitted,
                    HonoraryModel.bte_folio,
                ). \
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
                    "added_date": honorary.added_date,
                    "bte_emitted": int(getattr(honorary, "bte_emitted", 0) or 0),
                    "bte_folio": getattr(honorary, "bte_folio", None),
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
                "email": str(data.email) if data.email is not None else None,
                "address": str(data.address),
                "account_number": str(data.account_number),
                "start_date": str(data.start_date),
                "end_date": str(data.end_date),
                "amount": str(data.amount),
                "observation": str(data.observation),
                "bte_emitted": int(getattr(data, "bte_emitted", 0) or 0),
                "bte_folio": getattr(data, "bte_folio", None),
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
            blocked_rut = self.is_bte_sii_blocked_rut(
                honorary_inputs.replacement_employee_rut
            )
            should_emit_sii = (
                int(honorary_inputs.foreigner_id or 0) == 1 and not blocked_rut
            )
            # Solo marca Aceptado (2) si no requiere BTE. Con RUT queda Solicitado (14)
            # hasta que el SII confirme la emisión.
            honorary.status_id = 14 if should_emit_sii else 2
            if blocked_rut:
                honorary.bte_emitted = 0
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

            if blocked_rut and int(honorary_inputs.foreigner_id or 0) == 1:
                accept_msg = (
                    "Honorario aceptado (RUT excluido de emisión BTE en SII)"
                )
            elif should_emit_sii:
                accept_msg = "Datos guardados; pendiente emisión BTE en SII"
            else:
                accept_msg = "Honorario aceptado"

            return {
                "status": "success",
                "message": accept_msg,
                "id": honorary.id,
                "should_emit_sii": should_emit_sii,
                "status_id": honorary.status_id,
            }
        except Exception as e:
            error_message = str(e)
            return {"status": "error", "message": error_message}

    def send_by_id(self, id: int):
        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
        if not honorary:
            return {"status": "error", "message": "Honorario no encontrado"}
        if int(honorary.foreigner_id or 0) != 1:
            return {
                "status": "skipped",
                "message": "Sin RUT del trabajador: no se emite BTE en SII",
            }
        if self.is_bte_sii_blocked_rut(honorary.replacement_employee_rut):
            # No emitir al SII, pero dejar el honorario Aceptado (2) para no trabarlo.
            honorary.status_id = 2
            honorary.bte_emitted = 0
            honorary.updated_date = datetime.now()
            self.db.commit()
            return {
                "status": "skipped",
                "message": "RUT excluido: no se emite BTE en SII (honorario aceptado)",
                "bte_emitted": 0,
                "status_id": 2,
            }
        return self.send(honorary)
        
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

    def _keep_pending_for_sii_retry(self, honorary_id) -> None:
        """Si falla el SII, deja el honorario en Solicitado (14) para poder reaceptar."""
        if not honorary_id:
            return
        row = (
            self.db.query(HonoraryModel)
            .filter(HonoraryModel.id == honorary_id)
            .first()
        )
        if not row:
            return
        row.status_id = 14
        row.bte_emitted = 0
        row.updated_date = datetime.now()
        self.db.commit()

    def send(self, data):
        """Emite BTE ante el SII (Clave Tributaria) — reemplaza SimpleFactura BHE terceros."""
        honorary_id = getattr(data, "id", None)
        beneficiary_rut = str(getattr(data, "replacement_employee_rut", "") or "").strip()
        if self.is_bte_sii_blocked_rut(beneficiary_rut):
            if honorary_id:
                row = (
                    self.db.query(HonoraryModel)
                    .filter(HonoraryModel.id == honorary_id)
                    .first()
                )
                if row:
                    row.status_id = 2
                    row.bte_emitted = 0
                    row.updated_date = datetime.now()
                    self.db.commit()
            return {
                "status": "skipped",
                "message": "RUT excluido: no se emite BTE en SII (honorario aceptado)",
                "bte_emitted": 0,
                "status_id": 2,
            }
        try:
            from app.backend.classes.sii.bte import emit_bte
        except ModuleNotFoundError as e:
            print(f"Missing dependency for SII BTE: {e}")
            self._keep_pending_for_sii_retry(honorary_id)
            return {
                "status": "error",
                "message": f"Falta dependencia para BTE SII: {e}. Instale httpx en el venv del servicio.",
                "bte_emitted": 0,
                "status_id": 14,
            }

        settings = SettingClass(self.db).get()
        creds = SettingClass(self.db).get_sii_credentials()
        login_rut = creds.get("login_rut") or ""
        password = creds.get("password") or ""
        if not login_rut or not password:
            print("Clave Tributaria SII no configurada; no se emite BTE")
            self._keep_pending_for_sii_retry(honorary_id)
            return {
                "status": "error",
                "message": "Configure RUT y Clave Tributaria SII en Configuraciones",
                "bte_emitted": 0,
                "status_id": 14,
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
            self._keep_pending_for_sii_retry(honorary_id)
            return {"status": "error", "message": str(e), "bte_emitted": 0, "status_id": 14}

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

            confirmed = self._confirm_bte_in_sii(
                login_rut=login_rut,
                password=password,
                folio=result.folio,
                issue_date=date.today(),
            )
            # 1 = emitted (confirmed in SII list, or folio returned by emit)
            bte_emitted = 1 if (confirmed or result.folio) else 0

            if honorary_id:
                row = (
                    self.db.query(HonoraryModel)
                    .filter(HonoraryModel.id == honorary_id)
                    .first()
                )
                if row:
                    if bte_emitted == 1:
                        row.status_id = 2  # Aceptado solo si se emitió
                        row.bte_emitted = 1
                        row.bte_folio = int(result.folio) if result.folio else None
                        note = f"BTE SII folio {result.folio}"
                        if confirmed:
                            note += " (confirmada)"
                        prev = (row.observation or "").strip()
                        row.observation = f"{prev} | {note}".strip(" |") if prev else note
                        row.updated_date = datetime.now()
                        self.db.commit()
                    else:
                        self._keep_pending_for_sii_retry(honorary_id)
                        return {
                            "status": "error",
                            "message": "SII no confirmó la BTE; puede reintentar Aceptar",
                            "folio": result.folio,
                            "bte_emitted": 0,
                            "status_id": 14,
                        }
            return {
                "status": "success",
                "message": "Boleta de honorarios (BTE) emitida en SII",
                "folio": result.folio,
                "bte_emitted": bte_emitted,
                "confirmed_in_sii": bool(confirmed),
                "status_id": 2,
                "monto_bruto": result.monto_bruto,
                "retencion": result.retencion,
                "liquido": result.liquido,
            }
        except Exception as e:
            print(f"Error al emitir BTE en SII: {e}")
            self._keep_pending_for_sii_retry(honorary_id)
            return {
                "status": "error",
                "message": str(e),
                "bte_emitted": 0,
                "status_id": 14,
            }

    def _confirm_bte_in_sii(self, login_rut, password, folio, issue_date) -> bool:
        """Consulta BTE emitidas del mes en SII y busca el folio."""
        if not folio:
            return False
        try:
            from app.backend.classes.sii.bte import list_emitted

            items = list_emitted(
                login_rut=login_rut,
                password=password,
                year=issue_date.year,
                month=issue_date.month,
            )
            folio_int = int(folio)
            for item in items:
                if item.folio is not None and int(item.folio) == folio_int:
                    return True
            return False
        except Exception as e:
            print(f"No se pudo confirmar BTE folio={folio} en SII: {e}")
            return False

    def verify_bte_status(self, id: int):
        """Reconsulta SII y actualiza bte_emitted (1/0) para el honorario."""
        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
        if not honorary:
            return {"status": "error", "message": "Honorario no encontrado"}

        folio = honorary.bte_folio
        if not folio:
            # Try parse from observation: "BTE SII folio 123"
            obs = honorary.observation or ""
            m = re.search(r"folio\s+(\d+)", obs, re.I)
            if m:
                folio = int(m.group(1))
                honorary.bte_folio = folio

        if not folio:
            honorary.bte_emitted = 0
            honorary.updated_date = datetime.now()
            self.db.commit()
            return {
                "status": "success",
                "bte_emitted": 0,
                "bte_folio": None,
                "message": "Sin folio BTE; marcado como no emitida",
            }

        creds = SettingClass(self.db).get_sii_credentials()
        login_rut = creds.get("login_rut") or ""
        password = creds.get("password") or ""
        if not login_rut or not password:
            return {
                "status": "error",
                "message": "Configure RUT y Clave Tributaria SII en Configuraciones",
            }

        ref_date = honorary.updated_date.date() if honorary.updated_date else date.today()
        confirmed = self._confirm_bte_in_sii(
            login_rut=login_rut,
            password=password,
            folio=folio,
            issue_date=ref_date,
        )
        honorary.bte_emitted = 1 if confirmed else 0
        honorary.updated_date = datetime.now()
        self.db.commit()
        return {
            "status": "success",
            "bte_emitted": honorary.bte_emitted,
            "bte_folio": folio,
            "confirmed_in_sii": confirmed,
            "message": (
                f"BTE folio {folio} confirmada en SII"
                if confirmed
                else f"BTE folio {folio} no encontrada en SII del mes"
            ),
        }

    def _resolve_annul_bte_inputs(self, id: int, cause: str = "error_digitacion", folio: int | None = None):
        honorary = self.db.query(HonoraryModel).filter(HonoraryModel.id == id).first()
        if not honorary:
            return None, {"status": "error", "message": "Honorario no encontrado"}

        try:
            from app.backend.classes.sii.bte import ANNUL_CAUSES
        except ModuleNotFoundError as e:
            return None, {
                "status": "error",
                "message": f"Falta dependencia para BTE SII: {e}. Instale httpx en el venv del servicio.",
            }

        cause_key = (cause or "error_digitacion").strip()
        if cause_key not in ANNUL_CAUSES:
            return None, {
                "status": "error",
                "message": f"Motivo inválido. Use: {', '.join(ANNUL_CAUSES.keys())}",
            }

        target_folio = folio or honorary.bte_folio
        if not target_folio:
            obs = honorary.observation or ""
            m = re.search(r"folio\s+(\d+)", obs, re.I)
            if m:
                target_folio = int(m.group(1))
        if not target_folio:
            return None, {
                "status": "error",
                "message": "Indique el folio de la BTE a anular",
            }

        return {
            "honorary": honorary,
            "cause_key": cause_key,
            "folio": int(target_folio),
        }, None

    def prepare_annul_bte(self, id: int, cause: str = "error_digitacion", folio: int | None = None):
        """Paso 1: valida folio, motivo y credenciales SII."""
        resolved, err = self._resolve_annul_bte_inputs(id, cause, folio)
        if err:
            return err

        creds = SettingClass(self.db).get_sii_credentials()
        login_rut = creds.get("login_rut") or ""
        password = creds.get("password") or ""
        if not login_rut or not password:
            return {
                "status": "error",
                "message": "Configure RUT y Clave Tributaria SII en Configuraciones",
            }

        return {
            "status": "success",
            "message": "Datos validados; listo para anular en SII",
            "folio": resolved["folio"],
            "cause": resolved["cause_key"],
        }

    def annul_bte_sii(self, id: int, cause: str = "error_digitacion", folio: int | None = None):
        """Paso 2: anula la BTE en el portal SII."""
        resolved, err = self._resolve_annul_bte_inputs(id, cause, folio)
        if err:
            return err

        try:
            from app.backend.classes.sii.bte import annul_bte
        except ModuleNotFoundError as e:
            return {
                "status": "error",
                "message": f"Falta dependencia para BTE SII: {e}. Instale httpx en el venv del servicio.",
            }

        creds = SettingClass(self.db).get_sii_credentials()
        login_rut = creds.get("login_rut") or ""
        password = creds.get("password") or ""
        if not login_rut or not password:
            return {
                "status": "error",
                "message": "Configure RUT y Clave Tributaria SII en Configuraciones",
            }

        target_folio = resolved["folio"]
        cause_key = resolved["cause_key"]
        try:
            annul_bte(
                login_rut=login_rut,
                password=password,
                folio=int(target_folio),
                cause=cause_key,
            )
        except Exception as e:
            print(f"Error al anular BTE folio={target_folio}: {e}")
            return {"status": "error", "message": str(e)}

        return {
            "status": "success",
            "message": f"BTE folio {target_folio} anulada en SII",
            "folio": int(target_folio),
            "cause": cause_key,
        }

    def annul_bte_local(self, id: int, cause: str = "error_digitacion", folio: int | None = None):
        """Paso 3: actualiza el honorario en Intrajis (bte_emitted=0)."""
        resolved, err = self._resolve_annul_bte_inputs(id, cause, folio)
        if err:
            return err

        honorary = resolved["honorary"]
        target_folio = resolved["folio"]
        cause_key = resolved["cause_key"]
        cause_label = {
            "prestacion_no_efectuada": "Prestación no efectuada",
            "error_digitacion": "Error de digitación",
        }.get(cause_key, cause_key)

        honorary.bte_emitted = 0
        honorary.bte_folio = int(target_folio)
        note = f"BTE SII folio {target_folio} anulada ({cause_label})"
        prev = (honorary.observation or "").strip()
        honorary.observation = f"{prev} | {note}".strip(" |") if prev else note
        honorary.updated_date = datetime.now()
        self.db.commit()

        return {
            "status": "success",
            "message": "Honorario actualizado en Intrajis",
            "bte_emitted": 0,
            "bte_folio": int(target_folio),
            "cause": cause_key,
        }

    def annul_bte(self, id: int, cause: str = "error_digitacion", folio: int | None = None):
        """Anula BTE en SII y marca el honorario como no emitida (bte_emitted=0)."""
        prepared = self.prepare_annul_bte(id, cause, folio)
        if prepared.get("status") == "error":
            return prepared

        sii = self.annul_bte_sii(id, cause, folio)
        if sii.get("status") == "error":
            return sii

        local = self.annul_bte_local(id, cause, folio)
        if local.get("status") == "error":
            return {
                "status": "partial",
                "message": (
                    "BTE anulada en SII, pero no se pudo actualizar Intrajis: "
                    f"{local.get('message')}"
                ),
                "sii": sii,
                "local": local,
            }

        return {
            "status": "success",
            "message": f"BTE folio {sii.get('folio')} anulada en SII",
            "bte_emitted": 0,
            "bte_folio": sii.get("folio"),
            "cause": sii.get("cause"),
            "sii": sii,
            "local": local,
        }

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