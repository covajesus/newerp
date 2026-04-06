from typing import Optional

from fastapi import APIRouter, Depends, Query
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.schemas import BankStatement, DepositIds
from fastapi import UploadFile, File, HTTPException
from app.backend.classes.bank_statement_class import BankStatementClass
from datetime import datetime
import uuid

bank_statements = APIRouter(
    prefix="/bank_statements",
    tags=["BankStatement"]
)

@bank_statements.get("/compare_update_deposits")
def compare_update_deposits(
    db: Session = Depends(get_db)
):
    BankStatementClass(db).compare_update_deposits()

    return {"message": 'Uploaded successfully'}

@bank_statements.get("/history/list")
def list_bank_statement_histories(
    rut: Optional[str] = Query(None, description="RUT (coincidencia exacta normalizada)"),
    deposit_number: Optional[str] = Query(
        None, description="N° documento / depósito (exacto normalizado)"
    ),
    deposit_date: Optional[str] = Query(
        None, description="Fecha depósito YYYY-MM-DD (exacta)"
    ),
    amount: Optional[int] = Query(None, description="Monto (exacto)"),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Historial de cartolas (`bank_statement_histories`). `added_date` es cuándo se archivó la fila.
    Filtros opcionales por rut, deposit_number, deposit_date, amount.
    """
    return BankStatementClass(db).list_bank_statement_histories(
        rut=rut,
        deposit_number=deposit_number,
        deposit_date=deposit_date,
        amount=amount,
        page=page,
        items_per_page=items_per_page,
    )


@bank_statements.post("/get_comparation_pending_dtes_bank_statements")
def get_comparation_pending_dtes_bank_statements(
    db: Session = Depends(get_db)
):
    bank_statements = BankStatementClass(db).get_comparation_pending_dtes_bank_statements()

    return {"message": bank_statements}

@bank_statements.post("/get_comparation_pending_deposits_bank_statements")
def get_comparation_pending_deposits_bank_statements(
    db: Session = Depends(get_db)
):
    bank_statements = BankStatementClass(db).get_comparation_pending_deposits_bank_statements()

    return {"message": bank_statements}

@bank_statements.post("/store")
async def store(
    form_data: BankStatement = Depends(BankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        print(f"\n📥 [STORE] Iniciando carga de Excel...")
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'bank_statements'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        message = FileClass(db).upload(support, remote_path)
        file_url = FileClass(db).get(remote_path)

        if file_extension == "xlsx":
            # Guardar Excel
            print(f"📊 [STORE] Procesando Excel...")
            excel_data = BankStatementClass(db).read_store_bank_statement(remote_path, form_data.period)
            print(f"✅ [STORE] Excel guardado correctamente\n")
        else:
            raise HTTPException(status_code=400, detail="Formato no compatible")

        return {"message": message, "file_url": file_url, "data": excel_data}

    except Exception as e:
        print(f"❌ [STORE] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@bank_statements.get("/customer/accept/{bank_statement_id}/{folio}/{payment_date}")
def customer_accept(
    bank_statement_id: int,
    folio: int,
    payment_date: str,
    db: Session = Depends(get_db)
):
    message = BankStatementClass(db).customer_accept(bank_statement_id, folio, payment_date)

    return {"message": message}


@bank_statements.get("/customer/accept/{folio}/{payment_date}")
def customer_accept_legacy_folio_date(
    folio: int,
    payment_date: str,
    db: Session = Depends(get_db)
):
    """
    Compatibilidad: URL antigua con solo folio + fecha (2 segmentos tras /accept/).
    Resuelve bank_statement_id desde la vista de pendientes.
    La ruta de 3 segmentos va arriba; ésta solo coincide cuando hay exactamente 2 valores.
    """
    bsc = BankStatementClass(db)
    bs_id = bsc.resolve_bank_statement_id_for_pending_folio(folio)
    if bs_id is None:
        raise HTTPException(
            status_code=404,
            detail="No hay cartola pendiente para este folio o ya fue aplicada",
        )
    message = bsc.customer_accept(bs_id, folio, payment_date)
    return {"message": message}


@bank_statements.get("/deposit/accept/{id}")
def deposit_accept(
    id: int,
    db: Session = Depends(get_db)
):
    message = BankStatementClass(db).deposit_accept(id)

    return {"message": message}

@bank_statements.post("/deposit/massive_accept")
def massive_accept(data: DepositIds, db: Session = Depends(get_db)):
    results = []
    
    for deposit_id in data.deposit_ids:
        response = BankStatementClass(db).deposit_accept(deposit_id)
        results.append({"id": deposit_id, "message": response})

    return {"message": "Depósitos procesados correctamente", "details": results}