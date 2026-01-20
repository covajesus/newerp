from app.backend.db.models import EerrModel, ExpenseTypeModel, BranchOfficeModel, RemunerationModel
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
    """Clase para manejo de asientos contables"""
    
    # Constantes de configuración
    LIBREDTE_API_URL = "https://libredte.cl/api/lce/lce_asientos/buscar/76063822"
    LIBREDTE_TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
    BANCO_ACCOUNT = "Banco"
    
    def __init__(self, db):
        self.db = db
        self.auth_class = AuthenticationClass(db)
    
    def get_period_info(self, month: int, year: int) -> Tuple[str, str, str]:
        """
        Obtiene información del período: fechas de inicio, fin y período formateado
        
        Args:
            month: Mes (1-12)
            year: Año
            
        Returns:
            Tupla con (fecha_desde, fecha_hasta, período_formateado)
        """
        days_in_month = monthrange(year, month)[1]
        month_str = f"{month:02d}"
        
        since = f"{year}-{month_str}-01"
        until = f"{year}-{month_str}-{days_in_month:02d}"
        period = f"{year}-{month_str}"
        
        return since, until, period

    
    def clear_existing_data(self, period: str) -> None:
        """
        Elimina datos existentes del período
        
        Args:
            period: Período en formato YYYY-MM
        """
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
        """Obtiene headers para la API de LibreDTE"""
        return {
            'Authorization': f'Bearer {self.LIBREDTE_TOKEN}',
            'Content-Type': 'application/json'
        }
    
    def build_api_payload(self, since: str, until: str) -> Dict[str, str]:
        print(since, until)
        """Construye el payload para la API de LibreDTE"""
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
            "haber_hasta": ""
        }
    
    def fetch_external_data(self, since: str, until: str, rut: str, password: str) -> ApiResult:
        """
        Obtiene datos de la API externa de LibreDTE
        
        Args:
            since: Fecha desde
            until: Fecha hasta
            rut: RUT para renovar token si es necesario
            password: Password para renovar token
            
        Returns:
            ApiResult con los datos obtenidos
        """
        try:
            payload = self.build_api_payload(since, until)
            headers = self.get_api_headers()
            print(payload)
            
            response = requests.post(
                self.LIBREDTE_API_URL,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Si el token está inválido, crear uno nuevo del external_token
            if response.status_code == 401 or "token-invalido" in response.text.lower():
                print("Token LibreDTE inválido, renovando external_token...")
                self.auth_class.create_external_token(rut, password)
                
                # Reintentar petición con el mismo token LibreDTE
                response = requests.post(
                    self.LIBREDTE_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code == 200:
                return ApiResult(success=True, data=response.json())
            else:
                return ApiResult(
                    success=False, 
                    error=f"Error HTTP {response.status_code}: {response.text}"
                )
                
        except requests.RequestException as e:
            return ApiResult(success=False, error=f"Error de conexión: {str(e)}")
        except Exception as e:
            return ApiResult(success=False, error=f"Error inesperado: {str(e)}")

    
    def normalize_text(self, text: str) -> str:
        """Normaliza texto eliminando puntuación y espacios extra"""
        if not text:
            return ""
        # Eliminar puntos, comas, espacios extra y convertir a minúsculas
        import re
        normalized = re.sub(r'[.,\s]+', ' ', text.lower()).strip()
        return normalized
    
    def find_branch_office(self, description_parts: List[str]) -> Optional[BranchOfficeModel]:
        """
        Encuentra la sucursal basada en la descripción usando coincidencias flexibles
        
        Args:
            description_parts: Partes de la descripción dividida por '_'
            
        Returns:
            BranchOfficeModel encontrado o None
        """
        if not description_parts:
            return None
        
        search_term = description_parts[0]
  
        search_normalized = self.normalize_text(search_term)
        
        print(f"Buscando sucursal para: '{search_term}' (normalizado: '{search_normalized}')")
        
        # Buscar coincidencia exacta primero
        branch_office = self.db.query(BranchOfficeModel).filter(
            BranchOfficeModel.branch_office == search_term
        ).first()
        
        if branch_office:
            print(f"Encontrado con coincidencia exacta: {branch_office.branch_office}")
            return branch_office
        
        # Buscar por texto normalizado
        branch_offices = self.db.query(BranchOfficeModel).all()
        
        for bo in branch_offices:
            if not bo.branch_office:
                continue
                
            bo_normalized = self.normalize_text(bo.branch_office)
            
            # Coincidencia exacta normalizada
            if search_normalized == bo_normalized:
                print(f"Encontrado con coincidencia normalizada: {bo.branch_office}")
                return bo
            
            # Verificar si todas las palabras del término de búsqueda están en el nombre de la sucursal
            search_words = search_normalized.split()
            bo_words = bo_normalized.split()
            
            if len(search_words) >= 2:  # Solo si tenemos al menos 2 palabras para buscar
                matches = sum(1 for word in search_words if any(word in bo_word for bo_word in bo_words))
                # Si coinciden al menos el 80% de las palabras
                if matches >= len(search_words) * 0.8:
                    print(f"Encontrado con coincidencia parcial ({matches}/{len(search_words)} palabras): {bo.branch_office}")
                    return bo
        
        # Última oportunidad: buscar con LIKE
        for bo in branch_offices:
            if not bo.branch_office:
                continue
            if search_normalized in self.normalize_text(bo.branch_office):
                print(f"Encontrado con LIKE: {bo.branch_office}")
                return bo
        
        print(f"No se encontró sucursal para: '{search_term}'")
        return None
    
    def calculate_amount(self, detail_item: Dict, expense_type: Optional[ExpenseTypeModel], 
                        detail_description: str) -> float:
        """
        Calcula el monto final considerando debe/haber y positive_negative_id
        
        Args:
            detail_item: Item de detalle de la API
            expense_type: Tipo de gasto encontrado
            detail_description: Descripción completa del detalle
            
        Returns:
            Monto calculado
        """
        debe = detail_item.get('debe', '')
        haber = detail_item.get('haber', '')
        
        # Determinar monto base
        if debe:
            base_amount = float(debe)
        elif haber:
            base_amount = float(haber)
        else:
            return 0.0
        
        # Si no hay expense_type o positive_negative_id, retornar monto base
        if not expense_type or not hasattr(expense_type, 'positive_negative_id') or not expense_type.positive_negative_id:
            return base_amount
        
        multiplier = expense_type.positive_negative_id
        
        # Aplicar lógicas especiales para notas de crédito
        if 'NotaCredito' in detail_description:
            if 'NotaCreditoCompra' in detail_description:
                # Nota de crédito de compra: multiplicar por positive_negative_id al cuadrado y por -1
                return base_amount * multiplier * multiplier * -1
            else:
                # Nota de crédito normal: solo por -1
                return base_amount * -1
        else:
            # Caso normal: multiplicar por positive_negative_id
            return base_amount * multiplier
    
    def process_seat_details(self, seat_data: Dict, branch_office: BranchOfficeModel, 
                           period: str) -> Tuple[int, int]:
        """
        Procesa los detalles de un asiento
        
        Args:
            seat_data: Datos del asiento de la API
            branch_office: Sucursal encontrada
            period: Período en formato YYYY-MM
            
        Returns:
            Tupla con (procesados, omitidos)
        """
        processed = 0
        skipped = 0
        
        seat_id = seat_data.get('asiento', '')
        detail_description = seat_data.get('glosa', '')
        
        for detail_item in seat_data.get('detalle', []):
            try:
                # Saltar cuentas de banco
                if detail_item.get('cuenta_glosa') == self.BANCO_ACCOUNT:
                    skipped += 1
                    continue
                
                account_code = detail_item.get('cuenta_codigo', '')
                
                # Buscar tipo de gasto
                expense_type = self.db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.accounting_account == account_code
                ).first()
                
                # Calcular monto
                amount = self.calculate_amount(detail_item, expense_type, detail_description)
                
                # Crear registro EERR
                eerr = EerrModel(
                    branch_office_id=branch_office.id,
                    seat_id=seat_id,
                    period=period,
                    accounting_account=account_code,
                    amount=int(amount),  # Convertir a entero como en el original
                    added_date=datetime.now(),
                    updated_date=datetime.now()
                )
                
                self.db.add(eerr)
                processed += 1
                
            except Exception as e:
                print(f"Error procesando detalle del asiento {seat_id}: {str(e)}")
                skipped += 1
                continue
        
        return processed, skipped
    
    def process_external_results(self, results: List[Dict], period: str) -> ProcessingStats:
        """
        Procesa todos los resultados de la API externa
        
        Args:
            results: Lista de asientos de la API
            period: Período en formato YYYY-MM
            
        Returns:
            ProcessingStats con estadísticas del procesamiento
        """
        stats = ProcessingStats()
        print(results)
        for seat_data in results:
            try:
                # Obtener descripción y parsear sucursal
                glosa = seat_data.get('glosa', '')
                description_parts = glosa.split('_') if glosa else []
                
                # Encontrar sucursal
                branch_office = self.find_branch_office(description_parts)
                if not branch_office:
                    print(f"Sucursal no encontrada para: {description_parts[0] if description_parts else 'N/A'}")
                    stats.skipped_records += len(seat_data.get('detalle', []))
                    continue
                
                # Procesar detalles del asiento
                processed, skipped = self.process_seat_details(seat_data, branch_office, period)
                stats.processed_details += processed
                stats.skipped_records += skipped
                stats.processed_seats += 1
                
            except Exception as e:
                print(f"Error procesando asiento: {str(e)}")
                stats.skipped_records += len(seat_data.get('detalle', []))
                continue
        
        return stats
    
    def process_remunerations(self, period: str) -> int:
        """
        Procesa las remuneraciones del período
        
        Args:
            period: Período en formato YYYY-MM
            
        Returns:
            Número de remuneraciones procesadas
        """
        try:
            remunerations = self.db.query(RemunerationModel).filter(
                RemunerationModel.period == period
            ).all()
            
            processed_count = 0
            for remuneration in remunerations:
                eerr = EerrModel(
                    branch_office_id=remuneration.branch_office_id,
                    seat_id=None,  # Las remuneraciones no tienen seat_id
                    period=remuneration.period,
                    accounting_account=remuneration.accounting_account,
                    amount=remuneration.amount,
                    added_date=datetime.now(),
                    updated_date=datetime.now()
                )
                
                self.db.add(eerr)
                processed_count += 1
            
            return processed_count
            
        except Exception as e:
            raise Exception(f"Error procesando remuneraciones: {str(e)}")
    
    def refresh(self, external_token: str, rut: str, password: str, month: int, year: int) -> Dict:
        """
        Función principal para refrescar asientos contables
        
        Args:
            external_token: Token externo (para compatibilidad)
            rut: RUT para autenticación
            password: Password para autenticación
            month: Mes (1-12)
            year: Año
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        try:
            # Obtener información del período
            since, until, period = self.get_period_info(month, year)
            
            print(f"Iniciando refresh para período {period} ({since} a {until})")
            
            # Limpiar datos existentes
            self.clear_existing_data(period)
            
            # Obtener datos de la API externa
            api_result = self.fetch_external_data(since, until, rut, password)
            if not api_result.success:
                return {
                    "success": False,
                    "error": f"Error obteniendo datos externos: {api_result.error}"
                }
            
            # Procesar resultados externos
            stats = self.process_external_results(api_result.data, period)
            
            # Procesar remuneraciones
            remuneration_count = self.process_remunerations(period)
            stats.processed_remunerations = remuneration_count
            
            # Confirmar cambios
            self.db.commit()
            
            total_processed = stats.processed_details + stats.processed_remunerations
            
            return {
                "success": True,
                "message": f"Asientos procesados correctamente para {period}",
                "period": period,
                "date_range": f"{since} a {until}",
                "stats": {
                    "processed_seats": stats.processed_seats,
                    "processed_details": stats.processed_details,
                    "processed_remunerations": stats.processed_remunerations,
                    "skipped_records": stats.skipped_records,
                    "total_processed": total_processed
                }
            }
            
        except Exception as e:
            self.db.rollback()
            error_msg = f"Error al procesar asientos: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
