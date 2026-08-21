from app.backend.db.models import (
    EerrModel,
    ExpenseTypeModel,
    BranchOfficeModel,
    RemunerationModel,
    AccountingEntryModel,
    AccountingEntryLineModel,
    AccountingAccountModel,
)
from app.backend.classes.authentication_class import AuthenticationClass
from datetime import datetime
from calendar import monthrange
import requests
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ApiResult:
    """Estructura para resultados de la API"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None


@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    processed_seats: int = 0
    processed_details: int = 0
    processed_remunerations: int = 0
    skipped_records: int = 0


class SeatClass:
    """Clase para manejo de asientos contables / EERR"""

    # Constantes de configuración (LibreDTE legado; EERR ahora usa Intrajis)
    LIBREDTE_API_URL = "https://libredte.cl/api/lce/lce_asientos/buscar/76063822"
    LIBREDTE_TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
    BANCO_ACCOUNT = "Banco"

    def __init__(self, db):
        self.db = db
        self.auth_class = AuthenticationClass(db)

    def get_period_info(self, month: int, year: int) -> Tuple[str, str, str]:
        days_in_month = monthrange(year, month)[1]
        month_str = f"{month:02d}"
        since = f"{year}-{month_str}-01"
        until = f"{year}-{month_str}-{days_in_month:02d}"
        period = f"{year}-{month_str}"
        return since, until, period

    def clear_existing_data(self, period: str) -> None:
        try:
            deleted_count = self.db.query(EerrModel).filter(
                EerrModel.period == period
            ).delete()
            self.db.commit()
            print(f"Eliminados {deleted_count} registros existentes del período {period}")
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error al limpiar datos existentes: {str(e)}")

    def get_api_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.LIBREDTE_TOKEN}",
            "Content-Type": "application/json",
        }

    def build_api_payload(self, since: str, until: str) -> Dict[str, str]:
        return {
            "periodo": "",
            "fecha_desde": since,
            "fecha_hasta": until,
            "glosa": "",
            "operacion": "",
            "cuenta": "",
            "debe": "",
            "debe_desde": "",
            "debe_hasta": "",
            "haber": "",
            "haber_desde": "",
            "haber_hasta": "",
        }

    def fetch_external_data(self, since: str, until: str, rut: str, password: str) -> ApiResult:
        """Legado LibreDTE; EERR ya no lo usa."""
        try:
            payload = self.build_api_payload(since, until)
            headers = self.get_api_headers()
            response = requests.post(
                self.LIBREDTE_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            if response.status_code == 401 or "token-invalido" in response.text.lower():
                self.auth_class.create_external_token(rut, password)
                response = requests.post(
                    self.LIBREDTE_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
            if response.status_code == 200:
                return ApiResult(success=True, data=response.json())
            return ApiResult(
                success=False,
                error=f"Error HTTP {response.status_code}: {response.text}",
            )
        except requests.RequestException as e:
            return ApiResult(success=False, error=f"Error de conexión: {str(e)}")
        except Exception as e:
            return ApiResult(success=False, error=f"Error inesperado: {str(e)}")

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        import re
        return re.sub(r"[.,\s]+", " ", text.lower()).strip()

    def find_branch_office(self, description_parts: List[str]) -> Optional[BranchOfficeModel]:
        if not description_parts:
            return None

        search_term = description_parts[0]
        search_normalized = self.normalize_text(search_term)
        print(f"Buscando sucursal para: '{search_term}' (normalizado: '{search_normalized}')")

        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.branch_office == search_term
        ).first()
        if branch_office:
            return branch_office

        branch_offices = self.db.query(BranchOfficeModel).all()
        for bo in branch_offices:
            if not bo.branch_office:
                continue
            bo_normalized = self.normalize_text(bo.branch_office)
            if search_normalized == bo_normalized:
                return bo
            search_words = search_normalized.split()
            bo_words = bo_normalized.split()
            if len(search_words) >= 2:
                matches = sum(1 for word in search_words if any(word in bo_word for bo_word in bo_words))
                if matches >= len(search_words) * 0.8:
                    return bo

        for bo in branch_offices:
            if not bo.branch_office:
                continue
            if search_normalized in self.normalize_text(bo.branch_office):
                return bo

        print(f"No se encontró sucursal para: '{search_term}'")
        return None

    def calculate_amount(
        self,
        detail_item: Dict,
        expense_type: Optional[ExpenseTypeModel],
        detail_description: str,
    ) -> float:
        debe = detail_item.get("debe", "")
        haber = detail_item.get("haber", "")

        if debe:
            base_amount = float(debe)
        elif haber:
            base_amount = float(haber)
        else:
            return 0.0

        if (
            not expense_type
            or not hasattr(expense_type, "positive_negative_id")
            or not expense_type.positive_negative_id
        ):
            return base_amount

        multiplier = expense_type.positive_negative_id
        if "NotaCredito" in detail_description:
            if "NotaCreditoCompra" in detail_description:
                return base_amount * multiplier * multiplier
            return base_amount
        return base_amount * multiplier

    def _is_banco_line(self, account_code: str, concept: Optional[str]) -> bool:
        if (concept or "").strip() == self.BANCO_ACCOUNT:
            return True
        account = (
            self.db.query(AccountingAccountModel.name)
            .filter(AccountingAccountModel.code == str(account_code))
            .first()
        )
        if account and str(account[0] or "").strip() == self.BANCO_ACCOUNT:
            return True
        return False

    def process_intrajis_results(self, period: str) -> ProcessingStats:
        """Arma EERR desde asientos locales de Intrajis (accounting_entries)."""
        stats = ProcessingStats()
        entries = (
            self.db.query(AccountingEntryModel)
            .filter(
                AccountingEntryModel.period == period,
                AccountingEntryModel.annulled == 0,
            )
            .all()
        )

        for entry in entries:
            try:
                glosa = entry.glosa or ""
                description_parts = glosa.split("_") if glosa else []
                branch_office = self.find_branch_office(description_parts)
                if not branch_office:
                    print(
                        f"Sucursal no encontrada para: "
                        f"{description_parts[0] if description_parts else 'N/A'} "
                        f"(asiento local {entry.number})"
                    )
                    line_count = (
                        self.db.query(AccountingEntryLineModel)
                        .filter(AccountingEntryLineModel.accounting_entry_id == entry.id)
                        .count()
                    )
                    stats.skipped_records += line_count
                    continue

                lines = (
                    self.db.query(AccountingEntryLineModel)
                    .filter(AccountingEntryLineModel.accounting_entry_id == entry.id)
                    .order_by(AccountingEntryLineModel.sort_order.asc())
                    .all()
                )

                for line in lines:
                    try:
                        account_code = str(line.account_code or "").strip()
                        if not account_code:
                            stats.skipped_records += 1
                            continue
                        if self._is_banco_line(account_code, line.concept):
                            stats.skipped_records += 1
                            continue

                        detail_item = {
                            "debe": line.debit or "",
                            "haber": line.credit or "",
                            "cuenta_codigo": account_code,
                            "cuenta_glosa": line.concept or "",
                        }
                        expense_type = (
                            self.db.query(ExpenseTypeModel)
                            .filter(ExpenseTypeModel.accounting_account == account_code)
                            .first()
                        )
                        amount = self.calculate_amount(detail_item, expense_type, glosa)
                        if not amount:
                            stats.skipped_records += 1
                            continue

                        self.db.add(
                            EerrModel(
                                branch_office_id=branch_office.id,
                                seat_id=entry.number,
                                period=period,
                                accounting_account=account_code,
                                amount=int(amount),
                                added_date=datetime.now(),
                                updated_date=datetime.now(),
                            )
                        )
                        stats.processed_details += 1
                    except Exception as line_exc:
                        print(f"Error procesando línea del asiento local {entry.number}: {line_exc}")
                        stats.skipped_records += 1

                stats.processed_seats += 1
            except Exception as entry_exc:
                print(f"Error procesando asiento local: {entry_exc}")
                continue

        return stats

    def process_seat_details(
        self, seat_data: Dict, branch_office: BranchOfficeModel, period: str
    ) -> Tuple[int, int]:
        """Legado LibreDTE."""
        processed = 0
        skipped = 0
        seat_id = seat_data.get("asiento", "")
        detail_description = seat_data.get("glosa", "")

        for detail_item in seat_data.get("detalle", []):
            try:
                if detail_item.get("cuenta_glosa") == self.BANCO_ACCOUNT:
                    skipped += 1
                    continue
                account_code = detail_item.get("cuenta_codigo", "")
                expense_type = self.db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.accounting_account == account_code
                ).first()
                amount = self.calculate_amount(detail_item, expense_type, detail_description)
                self.db.add(
                    EerrModel(
                        branch_office_id=branch_office.id,
                        seat_id=seat_id,
                        period=period,
                        accounting_account=account_code,
                        amount=int(amount),
                        added_date=datetime.now(),
                        updated_date=datetime.now(),
                    )
                )
                processed += 1
            except Exception as e:
                print(f"Error procesando detalle del asiento {seat_id}: {str(e)}")
                skipped += 1
        return processed, skipped

    def process_external_results(self, results: List[Dict], period: str) -> ProcessingStats:
        """Legado LibreDTE."""
        stats = ProcessingStats()
        for seat_data in results:
            try:
                glosa = seat_data.get("glosa", "")
                description_parts = glosa.split("_") if glosa else []
                branch_office = self.find_branch_office(description_parts)
                if not branch_office:
                    stats.skipped_records += len(seat_data.get("detalle", []))
                    continue
                processed, skipped = self.process_seat_details(seat_data, branch_office, period)
                stats.processed_details += processed
                stats.skipped_records += skipped
                stats.processed_seats += 1
            except Exception as e:
                print(f"Error procesando asiento: {str(e)}")
                stats.skipped_records += len(seat_data.get("detalle", []))
        return stats

    def process_remunerations(self, period: str) -> int:
        try:
            remunerations = self.db.query(RemunerationModel).filter(
                RemunerationModel.period == period
            ).all()
            processed_count = 0
            for remuneration in remunerations:
                self.db.add(
                    EerrModel(
                        branch_office_id=remuneration.branch_office_id,
                        seat_id=None,
                        period=remuneration.period,
                        accounting_account=remuneration.accounting_account,
                        amount=remuneration.amount,
                        added_date=datetime.now(),
                        updated_date=datetime.now(),
                    )
                )
                processed_count += 1
            return processed_count
        except Exception as e:
            raise Exception(f"Error procesando remuneraciones: {str(e)}")

    def refresh(self, external_token: str, rut: str, password: str, month: int, year: int) -> Dict:
        """
        Refresca EERR desde asientos locales de Intrajis (+ remuneraciones).
        Ya no consulta LibreDTE.
        """
        try:
            since, until, period = self.get_period_info(month, year)
            print(f"Iniciando refresh EERR desde Intrajis para período {period} ({since} a {until})")

            self.clear_existing_data(period)
            stats = self.process_intrajis_results(period)
            remuneration_count = self.process_remunerations(period)
            stats.processed_remunerations = remuneration_count
            self.db.commit()

            total_processed = stats.processed_details + stats.processed_remunerations
            return {
                "success": True,
                "message": f"EERR armado desde Intrajis para {period}",
                "source": "intrajis",
                "period": period,
                "date_range": f"{since} a {until}",
                "stats": {
                    "processed_seats": stats.processed_seats,
                    "processed_details": stats.processed_details,
                    "processed_remunerations": stats.processed_remunerations,
                    "skipped_records": stats.skipped_records,
                    "total_processed": total_processed,
                },
            }
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error al procesar EERR desde Intrajis: {str(e)}"
            print(error_msg)
            return {"success": False, "error": error_msg}
