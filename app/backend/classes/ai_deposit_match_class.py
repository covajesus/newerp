from datetime import datetime
from sqlalchemy.orm import Session
from app.backend.db.models import (
    AiDepositMatchModel,
    BankStatementModel,
    DepositModel,
    TransbankStatementModel,
    BranchOfficeModel
)
from fastapi import HTTPException
from typing import List, Optional, Dict
from openai import OpenAI
import os
import time
import json

class AiDepositMatchClass:
    def __init__(self, db: Session):
        self.db = db
        self._client = None
        self._api_key = None
    
    @property
    def client(self):
        """Lazy initialization del cliente de OpenAI"""
        if self._client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="OPENAI_API_KEY no está configurada en las variables de entorno")
            self._api_key = api_key
            try:
                self._client = OpenAI(api_key=api_key)
            except (RuntimeError, SystemError) as e:
                # Capturar errores relacionados con atexit/shutdown
                if "atexit" in str(e).lower() or "shutdown" in str(e).lower():
                    print(f"Advertencia: No se pudo inicializar cliente OpenAI debido a que el proceso está cerrando: {str(e)}")
                    # No lanzar excepción, solo retornar None para que el procesamiento continúe sin IA
                    return None
                else:
                    print(f"Error al inicializar cliente OpenAI: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error al inicializar cliente OpenAI: {str(e)}")
            except Exception as e:
                print(f"Error al inicializar cliente OpenAI: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error al inicializar cliente OpenAI: {str(e)}")
        return self._client
    
    def find_matches_with_ai(self, bank_statement_id: Optional[int] = None, transbank_statement_id: Optional[int] = None):
        """
        Busca matches entre bank statements/transbank statements y deposits usando IA
        """
        try:
            # Obtener datos de la cartola (bank statement o transbank statement)
            if bank_statement_id:
                bank_statement = self.db.query(BankStatementModel).filter(
                    BankStatementModel.id == bank_statement_id
                ).first()
                if not bank_statement:
                    raise HTTPException(status_code=404, detail="Bank statement no encontrado")
                
                excel_data = {
                    'deposit_number': bank_statement.deposit_number,
                    'branch_office': None,  # No hay sucursal directa en bank_statement
                    'amount': bank_statement.amount,
                    'date': bank_statement.deposit_date
                }
                transbank_statement_id_value = None
                bank_statement_id_value = bank_statement_id
            elif transbank_statement_id:
                transbank_statement = self.db.query(TransbankStatementModel).filter(
                    TransbankStatementModel.id == transbank_statement_id
                ).first()
                if not transbank_statement:
                    raise HTTPException(status_code=404, detail="Transbank statement no encontrado")
                
                # Convertir amount de string a int si es posible
                try:
                    amount = int(float(transbank_statement.amount)) if transbank_statement.amount else None
                except (ValueError, TypeError):
                    amount = None
                
                excel_data = {
                    'deposit_number': transbank_statement.code,  # El código puede ser el número de referencia
                    'branch_office': transbank_statement.branch_office_name,
                    'amount': amount,
                    'date': transbank_statement.original_date
                }
                transbank_statement_id_value = transbank_statement_id
                bank_statement_id_value = None
            else:
                raise HTTPException(status_code=400, detail="Debe proporcionar bank_statement_id o transbank_statement_id")
            
            # Buscar depósitos candidatos
            print(f"   🔍 [FIND_MATCHES] Buscando depósitos candidatos...")
            candidates = self._find_candidate_deposits(excel_data)
            print(f"   📊 [FIND_MATCHES] Candidatos encontrados: {len(candidates)}")
            
            if not candidates:
                print(f"   ⚠️  [FIND_MATCHES] No hay candidatos, retornando")
                return {
                    "status": "no_candidates",
                    "message": "No se encontraron depósitos candidatos",
                    "excel_data": excel_data
                }
            
            # Usar IA para encontrar el mejor match
            print(f"   🤖 [FIND_MATCHES] Llamando a _ai_match con {len(candidates)} candidatos...")
            best_match = self._ai_match(excel_data, candidates)
            print(f"   📊 [FIND_MATCHES] Resultado de _ai_match: {'Match encontrado' if best_match else 'No match'}")
            
            if best_match:
                # Guardar el match en la base de datos
                match_record = self._save_match(
                    bank_statement_id=bank_statement_id_value,
                    transbank_statement_id=transbank_statement_id_value if 'transbank_statement_id_value' in locals() else None,
                    excel_data=excel_data,
                    deposit_data=best_match['deposit'],
                    match_info=best_match['match_info']
                )
                
                return {
                    "status": "success",
                    "match_id": match_record.id,
                    "confidence": best_match['match_info']['confidence'],
                    "reason": best_match['match_info']['reason'],
                    "deposit_id": best_match['deposit']['id']
                }
            else:
                print(f"   ⚠️  [FIND_MATCHES] No se encontró match confiable")
                return {
                    "status": "no_match",
                    "message": "La IA no encontró un match confiable",
                    "candidates_count": len(candidates)
                }
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al buscar matches con IA: {str(e)}")
    
    def _find_candidate_deposits(self, excel_data: Dict) -> List[Dict]:
        """
        Encuentra depósitos candidatos usando estrategia humana:
        1. Primero buscar por monto (rango amplio)
        2. Luego filtrar por sucursal si está disponible
        3. Incluir TODOS los depósitos para que la IA analice (no se filtran por status)
        """
        candidates = []
        
        # ESTRATEGIA 1: Buscar por monto (lo más importante)
        # Rango amplio: ±10% para capturar variaciones
        if excel_data.get('amount'):
            amount = excel_data['amount']
            min_amount = int(amount * 0.90)  # -10%
            max_amount = int(amount * 1.10)  # +10%
            
            # Buscar depósitos con monto similar
            # No filtramos por status_id para que la IA analice todos los depósitos
            # La IA decidirá cuál es el mejor match independientemente del status
            deposits = self.db.query(DepositModel).filter(
                (DepositModel.collection_amount.between(min_amount, max_amount)) |
                (DepositModel.deposited_amount.between(min_amount, max_amount))
            ).limit(200).all()  # Más candidatos para análisis
            
            for deposit in deposits:
                # Obtener nombre de sucursal
                branch_office = None
                if deposit.branch_office_id:
                    branch = self.db.query(BranchOfficeModel).filter(
                        BranchOfficeModel.id == deposit.branch_office_id
                    ).first()
                    branch_office = branch.branch_office if branch else None
                
                candidates.append({
                    'id': deposit.id,
                    'payment_number': deposit.payment_number,
                    'branch_office_id': deposit.branch_office_id,
                    'branch_office_name': branch_office,
                    'collection_amount': deposit.collection_amount,
                    'deposited_amount': deposit.deposited_amount,
                    'collection_date': deposit.collection_date,
                    'deposit_date': deposit.deposit_date
                })
        
        # Si no hay candidatos por monto, buscar por número de depósito como fallback
        if not candidates and excel_data.get('deposit_number'):
            deposit_number = str(excel_data['deposit_number']).strip()
            
            # Buscar depósitos con payment_number similar (más flexible)
            # No filtramos por status_id para que la IA analice todos los depósitos
            deposits = self.db.query(DepositModel).filter(
                DepositModel.payment_number.like(f"%{deposit_number}%")
            ).limit(100).all()
            
            for deposit in deposits:
                branch_office = None
                if deposit.branch_office_id:
                    branch = self.db.query(BranchOfficeModel).filter(
                        BranchOfficeModel.id == deposit.branch_office_id
                    ).first()
                    branch_office = branch.branch_office if branch else None
                
                candidates.append({
                    'id': deposit.id,
                    'payment_number': deposit.payment_number,
                    'branch_office_id': deposit.branch_office_id,
                    'branch_office_name': branch_office,
                    'collection_amount': deposit.collection_amount,
                    'deposited_amount': deposit.deposited_amount,
                    'collection_date': deposit.collection_date,
                    'deposit_date': deposit.deposit_date
                })
        
        # Eliminar duplicados por ID
        seen_ids = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate['id'] not in seen_ids:
                seen_ids.add(candidate['id'])
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    def _ai_match(self, excel_data: Dict, candidates: List[Dict]) -> Optional[Dict]:
        """
        Usa OpenAI para encontrar el mejor match entre excel_data y candidates
        """
        if not candidates:
            print(f"   ⚠️  [AI_MATCH] No hay candidatos, retornando None")
            return None
        
        try:
            print(f"   📝 [AI_MATCH] Construyendo prompt... (candidatos: {len(candidates)})")
            # Construir el prompt para OpenAI
            prompt = self._build_matching_prompt(excel_data, candidates)
            prompt_length = len(prompt)
            print(f"   📝 [AI_MATCH] Prompt construido ({prompt_length} caracteres)")
            
            start_time = time.time()
            print(f"   🔄 [AI_MATCH] Iniciando llamada a OpenAI API... (modelo: gpt-4o-mini)")
            
            # Llamar a OpenAI API
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Usar modelo más económico
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un analista financiero experto con años de experiencia. Tu tarea es encontrar matches entre datos de cartolas bancarias (Excel) y depósitos en base de datos, analizando como lo haría un humano experimentado. Eres flexible pero riguroso: aceptas variaciones normales pero solo sugieres matches con alta confianza. Analizas monto primero (lo más importante), luego sucursal, luego número de depósito, y finalmente fechas, considerando todos los factores en conjunto. Eres mente abierta: si monto y sucursal coinciden pero el número es diferente, aún así puedes sugerir el match si hay razones válidas (fechas cercanas, contexto, etc.)."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,  # Ligeramente más alta para permitir análisis más creativo pero aún determinístico
                    max_tokens=800  # Más tokens para explicaciones detalladas
                )
                print(f"   ✅ [AI_MATCH] Respuesta recibida de OpenAI API")
            except Exception as api_error:
                print(f"   ❌ [AI_MATCH] Error en llamada a OpenAI API: {str(api_error)}")
                raise
            
            processing_time = int((time.time() - start_time) * 1000)
            print(f"   ⏱️  [AI_MATCH] Tiempo de procesamiento: {processing_time}ms")
            
            # Parsear respuesta
            print(f"   📄 [AI_MATCH] Parseando respuesta de OpenAI...")
            response_text = response.choices[0].message.content
            print(f"   📄 [AI_MATCH] Respuesta recibida ({len(response_text)} caracteres)")
            match_result = self._parse_ai_response(response_text, candidates)
            print(f"   📊 [AI_MATCH] Resultado del parseo: {'Match encontrado' if match_result else 'No match'}")
            
            if match_result:
                match_result['match_info']['ai_model_used'] = response.model
                match_result['match_info']['ai_prompt_tokens'] = response.usage.prompt_tokens
                match_result['match_info']['ai_completion_tokens'] = response.usage.completion_tokens
                match_result['match_info']['processing_time_ms'] = processing_time
            
            return match_result
            
        except (RuntimeError, SystemError) as e:
            # Capturar errores relacionados con atexit/shutdown
            error_str = str(e).lower()
            if "atexit" in error_str or "shutdown" in error_str:
                # No loguear este error, es esperado cuando el proceso se cierra durante el procesamiento
                # Simplemente retornar None para que el procesamiento continúe
                return None
            else:
                print(f"⚠️  Error en _ai_match: {str(e)}")
            return None
        except Exception as e:
            print(f"Error en _ai_match: {str(e)}")
            return None
    
    def _build_matching_prompt(self, excel_data: Dict, candidates: List[Dict]) -> str:
        """
        Construye el prompt para OpenAI con análisis humano y flexible
        """
        prompt = f"""Eres un analista financiero experto. Tu tarea es encontrar matches entre datos de una cartola bancaria (Excel) y depósitos en la base de datos, incluso cuando los datos no coinciden exactamente.

ANÁLISIS REQUERIDO (en este orden, como lo haría un humano):

DATOS DE LA CARTOLA (Excel):
- Número de depósito: {excel_data.get('deposit_number', 'N/A')}
- Sucursal: {excel_data.get('branch_office', 'N/A')}
- Monto: {excel_data.get('amount', 'N/A')}
- Fecha: {excel_data.get('date', 'N/A')}

CANDIDATOS EN BASE DE DATOS (depósitos no aceptados):
"""
        
        # Limitar a 30 candidatos para no exceder tokens
        for i, candidate in enumerate(candidates[:30], 1):
            prompt += f"""
Candidato {i}:
- ID Depósito: {candidate['id']}
- Número de pago: {candidate['payment_number']}
- Sucursal: {candidate['branch_office_name'] or 'N/A'} (ID: {candidate['branch_office_id']})
- Monto cobrado: {candidate['collection_amount']}
- Monto depositado: {candidate['deposited_amount']}
- Fecha de cobro: {candidate['collection_date']}
- Fecha de depósito: {candidate['deposit_date']}
"""
        
        prompt += """
METODOLOGÍA DE ANÁLISIS (como un humano):

PASO 1 - ANÁLISIS DE MONTO (PRIORITARIO):
- Compara el monto de la cartola con collection_amount y deposited_amount
- Acepta diferencias pequeñas (±5% o menos) como posibles matches
- Si hay diferencia, analiza si puede ser por comisiones, redondeos, etc.

PASO 2 - ANÁLISIS DE SUCURSAL:
- Compara el nombre de sucursal de la cartola con el del candidato
- Sé flexible: "Centro" puede ser igual a "Sucursal Centro", "Centro Principal", etc.
- Ignora diferencias de mayúsculas/minúsculas, acentos, espacios extra
- Si la cartola no tiene sucursal, no descartes el candidato por esto

PASO 3 - ANÁLISIS DE NÚMERO DE DEPÓSITO:
- Compara el número de depósito de la cartola con payment_number
- Acepta variaciones: "12345" puede ser igual a "1234", "123456", "012345", etc.
- Considera que pueden tener prefijos/sufijos diferentes
- Si los números son muy diferentes, NO descartes si el monto y sucursal coinciden

PASO 4 - ANÁLISIS DE FECHA (REFUERZO):
- Compara las fechas si están disponibles
- Acepta fechas cercanas (mismo día, día anterior/siguiente)
- Si hay diferencia de fechas pero monto y sucursal coinciden, puede ser válido

PASO 5 - ANÁLISIS INTEGRAL:
- Evalúa TODOS los factores juntos
- Si monto y sucursal coinciden pero número es diferente, analiza si puede ser el mismo depósito
- Si monto coincide exactamente y fecha es cercana, es muy probable que sea el mismo
- Sé creativo pero conservador: solo sugiere matches con alta confianza

RESPUESTA REQUERIDA (formato JSON):
Si encuentras un match confiable (confidence >= 70):
{
  "candidate_id": <ID del candidato>,
  "confidence": <0-100, siendo 100 = match perfecto>,
  "reason": "<explicación detallada del análisis: por qué crees que es el mismo depósito, qué factores coinciden, qué diferencias hay y por qué aún así es válido>"
}

Si NO hay match confiable (confidence < 70):
{
  "match": false,
  "reason": "<explicación de por qué no hay match confiable>"
}

IMPORTANTE:
- Sé mente abierta pero rigurosa
- Analiza como un humano: considera contexto, variaciones normales, errores de captura
- Prioriza matches donde monto y sucursal coinciden, incluso si el número es diferente
- Solo sugiere matches con confidence >= 70
"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Parsea la respuesta de OpenAI
        """
        try:
            # Intentar extraer JSON de la respuesta
            response_text = response_text.strip()
            
            # Buscar JSON en la respuesta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return None
            
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Verificar si hay match
            if result.get('match') == False:
                return None
            
            # Obtener el candidato seleccionado
            candidate_id = result.get('candidate_id')
            if not candidate_id:
                return None
            
            candidate = next((c for c in candidates if c['id'] == candidate_id), None)
            if not candidate:
                return None
            
            confidence = result.get('confidence', 0)
            if confidence < 70:  # Solo aceptar matches con confianza >= 70%
                return None
            
            return {
                'deposit': candidate,
                'match_info': {
                    'confidence': confidence,
                    'reason': result.get('reason', 'Match encontrado por IA')
                }
            }
            
        except Exception as e:
            print(f"Error parseando respuesta de IA: {str(e)}")
            return None
    
    def _save_match(self, bank_statement_id: Optional[int], transbank_statement_id: Optional[int],
                   excel_data: Dict, deposit_data: Dict, match_info: Dict) -> AiDepositMatchModel:
        """
        Guarda el match en la base de datos.
        IMPORTANTE: Solo guarda el match en ai_deposit_matches, NO acepta el depósito automáticamente.
        El depósito mantiene su status_id original sin cambios.
        """
        match_record = AiDepositMatchModel(
            bank_statement_id=bank_statement_id,
            transbank_statement_id=transbank_statement_id,
            excel_deposit_number=str(excel_data.get('deposit_number', '')),
            excel_branch_office=excel_data.get('branch_office'),
            excel_amount=excel_data.get('amount'),
            excel_date=excel_data.get('date'),
            db_deposit_id=deposit_data['id'],
            db_branch_office_id=deposit_data['branch_office_id'],
            db_branch_office_name=deposit_data['branch_office_name'],
            db_payment_number=deposit_data['payment_number'],
            db_collection_amount=deposit_data['collection_amount'],
            db_deposited_amount=deposit_data['deposited_amount'],
            db_collection_date=deposit_data['collection_date'],
            match_confidence=match_info.get('confidence'),
            match_reason=match_info.get('reason'),
            match_type='ai_suggested',
            is_confirmed=False,
            is_rejected=False,
            ai_model_used=match_info.get('ai_model_used'),
            ai_prompt_tokens=match_info.get('ai_prompt_tokens'),
            ai_completion_tokens=match_info.get('ai_completion_tokens'),
            processing_time_ms=match_info.get('processing_time_ms')
        )
        
        self.db.add(match_record)
        self.db.commit()
        self.db.refresh(match_record)
        
        return match_record
    
    def confirm_match(self, match_id: int, user_id: Optional[int] = None):
        """
        Confirma un match encontrado por IA
        """
        match = self.db.query(AiDepositMatchModel).filter(
            AiDepositMatchModel.id == match_id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match no encontrado")
        
        match.is_confirmed = True
        match.confirmed_by_user_id = user_id
        match.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return match
    
    def reject_match(self, match_id: int, user_id: Optional[int] = None):
        """
        Rechaza un match encontrado por IA
        """
        match = self.db.query(AiDepositMatchModel).filter(
            AiDepositMatchModel.id == match_id
        ).first()
        
        if not match:
            raise HTTPException(status_code=404, detail="Match no encontrado")
        
        match.is_rejected = True
        match.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return match
    
    def get_matches(self, is_confirmed: Optional[bool] = None, is_rejected: Optional[bool] = None,
                   limit: int = 100, offset: int = 0):
        """
        Obtiene los matches guardados
        """
        query = self.db.query(AiDepositMatchModel)
        
        if is_confirmed is not None:
            query = query.filter(AiDepositMatchModel.is_confirmed == is_confirmed)
        
        if is_rejected is not None:
            query = query.filter(AiDepositMatchModel.is_rejected == is_rejected)
        
        query = query.order_by(AiDepositMatchModel.created_at.desc())
        total = query.count()
        
        matches = query.offset(offset).limit(limit).all()
        
        return {
            "total": total,
            "matches": matches
        }
    
    def process_all_pending_bank_statements(self, limit: Optional[int] = None):
        """
        Procesa todos los registros de bank_statements que aún no tienen match confirmado,
        analizándolos uno por uno con IA contra depósitos no aceptados
        """
        try:
            print(f"🔍 Buscando bank_statements pendientes de procesar...")
            
            # Obtener IDs de bank_statements que ya tienen match confirmado
            confirmed_bank_statement_ids = self.db.query(AiDepositMatchModel.bank_statement_id).filter(
                AiDepositMatchModel.is_confirmed == True,
                AiDepositMatchModel.bank_statement_id.isnot(None)
            ).distinct().all()
            
            confirmed_ids_list = [row[0] for row in confirmed_bank_statement_ids]
            print(f"📋 Bank statements con match confirmado: {len(confirmed_ids_list)}")
            
            # Obtener todos los bank_statements que no tienen match confirmado
            query = self.db.query(BankStatementModel)
            
            if confirmed_ids_list:
                query = query.filter(
                    ~BankStatementModel.id.in_(confirmed_ids_list)
                )
            
            if limit:
                query = query.limit(limit)
            
            bank_statements = query.all()
            total_to_process = len(bank_statements)
            print(f"📊 Total de bank_statements a procesar: {total_to_process}")
            
            results = {
                "total_processed": 0,
                "matched": 0,
                "no_match": 0,
                "matches_found": 0,
                "errors": []
            }
            
            for idx, bank_statement in enumerate(bank_statements, 1):
                try:
                    # Verificar si el proceso está cerrando antes de continuar
                    import sys
                    if not sys.stdin.isatty() and hasattr(sys, '_getframe'):
                        # Si estamos en un proceso que se está cerrando, salir gracefully
                        pass
                    
                    # Asegurar que la sesión esté activa antes de cada procesamiento
                    try:
                        self.db.commit()
                    except Exception as commit_error:
                        if "closed" in str(commit_error).lower() or "shutdown" in str(commit_error).lower():
                            print(f"⚠️  Sesión de BD cerrada, deteniendo procesamiento de IA...")
                            break
                        raise
                    
                    if idx % 10 == 0 or idx == 1:
                        print(f"   Procesando registro {idx}/{total_to_process} (ID: {bank_statement.id})...")
                    
                    try:
                        print(f"   🔍 [REGISTRO {idx}] Buscando candidatos para bank_statement_id={bank_statement.id}...")
                        result = self.find_matches_with_ai(bank_statement_id=bank_statement.id)
                        print(f"   ✅ [REGISTRO {idx}] Procesamiento completado. Status: {result.get('status', 'unknown')}")
                        results["total_processed"] += 1
                        
                        if result and result.get("status") == "success":
                            results["matched"] += 1
                            results["matches_found"] += 1
                            if idx % 10 == 0 or idx == 1:
                                print(f"   ✅ Match encontrado! Confianza: {result.get('confidence', 'N/A')}")
                        else:
                            results["no_match"] += 1
                    except (RuntimeError, SystemError) as ai_error:
                        # Capturar errores de atexit/shutdown específicamente
                        if "atexit" in str(ai_error).lower() or "shutdown" in str(ai_error).lower():
                            print(f"⚠️  Proceso cerrando, deteniendo procesamiento de IA en registro {idx}...")
                            break
                        else:
                            raise
                        
                except Exception as e:
                    # Si el error es por sesión cerrada o proceso cerrando, salir
                    error_str = str(e).lower()
                    if "closed" in error_str or "shutdown" in error_str or "atexit" in error_str:
                        print(f"⚠️  Proceso cerrando, deteniendo procesamiento de IA...")
                        break
                    
                    results["errors"].append({
                        "bank_statement_id": bank_statement.id,
                        "error": str(e)
                    })
                    # Continuar con el siguiente registro aunque haya un error
                    try:
                        self.db.rollback()
                    except:
                        pass  # Si la sesión está cerrada, no hacer rollback
                    
                    if idx % 10 == 0:
                        print(f"   ⚠️  Error en registro {idx}: {str(e)[:100]}")
                    continue
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar bank statements pendientes: {str(e)}")
    
    def process_all_pending_transbank_statements(self, limit: Optional[int] = None):
        """
        Procesa todos los registros de transbank_statements que aún no tienen match confirmado,
        analizándolos uno por uno con IA contra depósitos no aceptados
        """
        try:
            # Obtener IDs de transbank_statements que ya tienen match confirmado
            confirmed_transbank_ids = self.db.query(AiDepositMatchModel.transbank_statement_id).filter(
                AiDepositMatchModel.is_confirmed == True,
                AiDepositMatchModel.transbank_statement_id.isnot(None)
            ).distinct().all()
            
            confirmed_ids_list = [row[0] for row in confirmed_transbank_ids]
            
            # Obtener todos los transbank_statements que no tienen match confirmado
            query = self.db.query(TransbankStatementModel)
            
            if confirmed_ids_list:
                query = query.filter(
                    ~TransbankStatementModel.id.in_(confirmed_ids_list)
                )
            
            if limit:
                query = query.limit(limit)
            
            transbank_statements = query.all()
            
            results = {
                "total_processed": 0,
                "matched": 0,
                "no_match": 0,
                "matches_found": 0,
                "errors": []
            }
            
            for transbank_statement in transbank_statements:
                try:
                    # Asegurar que la sesión esté activa antes de cada procesamiento
                    self.db.commit()
                    
                    result = self.find_matches_with_ai(transbank_statement_id=transbank_statement.id)
                    results["total_processed"] += 1
                    
                    if result.get("status") == "success":
                        results["matched"] += 1
                        results["matches_found"] += 1
                    else:
                        results["no_match"] += 1
                        
                except Exception as e:
                    results["errors"].append({
                        "transbank_statement_id": transbank_statement.id,
                        "error": str(e)
                    })
                    # Continuar con el siguiente registro aunque haya un error
                    self.db.rollback()
                    continue
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al procesar transbank statements pendientes: {str(e)}")
