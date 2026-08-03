from fastapi import APIRouter, Depends
from app.backend.db.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from app.backend.classes.file_class import FileClass
from app.backend.schemas import TransbankStatement, TransbankStatementList
from fastapi import UploadFile, File, HTTPException
from app.backend.classes.transbank_statement_class import TransbankStatementClass
from datetime import datetime
import uuid
from fastapi.responses import StreamingResponse
import json
import queue
import threading

transbank_statements = APIRouter(
    prefix="/transbank_statements",
    tags=["TransbankStatements"]
)

@transbank_statements.post("/")
def index(transbank: TransbankStatementList, db: Session = Depends(get_db)):
    data = TransbankStatementClass(db).get_all(transbank.page)

    return {"message": data}

@transbank_statements.post("/store")
def store(
    form_data: TransbankStatement = Depends(TransbankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if '.' in support.filename else ''
        file_category_name = 'transbank_statements'
        unique_filename = f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"

        remote_path = f"{file_category_name}_{unique_filename}"

        print("🔄 Subiendo archivo...")
        message = FileClass(db).upload(support, remote_path)
        file_url = FileClass(db).get(remote_path)
        print(f"✅ Archivo subido: {file_url}")

        # Procesar el archivo sincrónicamente - esperar hasta que termine
        print("🔄 Iniciando procesamiento...")
        result = TransbankStatementClass(db).read_store_bank_statement(file_url, form_data.period)
        print(f"✅ Procesamiento completado con resultado: {result}")
        
        if result == 1:
            return {
                "message": "Cartola de transbank procesada exitosamente", 
                "file_url": file_url,
                "status": "completed"
            }
        else:
            raise HTTPException(status_code=500, detail="Error al procesar la cartola")

    except Exception as e:
        print(f"❌ Error en store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar: {str(e)}")

@transbank_statements.post("/store_with_progress")
def store_with_progress(
    form_data: TransbankStatement = Depends(TransbankStatement.as_form),
    support: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Sube el .dat y procesa emitiendo progreso en vivo (NDJSON).
    Cada línea: {"type":"progress","progress":N,"message":"..."}
    Final: {"type":"done",...} o {"type":"error","detail":"..."}
    """
    try:
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        unique_id = uuid.uuid4().hex[:8]
        file_extension = support.filename.split('.')[-1] if support and '.' in (support.filename or '') else ''
        file_category_name = 'transbank_statements'
        unique_filename = (
            f"{timestamp}_{unique_id}.{file_extension}" if file_extension else f"{timestamp}_{unique_id}"
        )
        remote_path = f"{file_category_name}_{unique_filename}"
        period = form_data.period

        FileClass(db).upload(support, remote_path)
        file_url = FileClass(db).get(remote_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    def event_stream():
        events: queue.Queue = queue.Queue()

        def capture_progress(progress, message):
            events.put(
                {
                    "type": "progress",
                    "progress": float(progress),
                    "message": str(message),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        def worker():
            worker_db = SessionLocal()
            try:
                capture_progress(0, "Iniciando procesamiento...")
                result = TransbankStatementClass(worker_db).read_store_bank_statement(
                    file_url,
                    period,
                    progress_callback=capture_progress,
                )
                if result == 1:
                    capture_progress(100, "Procesamiento completado exitosamente")
                    events.put(
                        {
                            "type": "done",
                            "status": "completed",
                            "message": "Cartola de transbank procesada exitosamente",
                            "file_url": file_url,
                        }
                    )
                else:
                    events.put(
                        {
                            "type": "error",
                            "detail": "Error al procesar la cartola",
                        }
                    )
            except Exception as exc:
                events.put(
                    {
                        "type": "error",
                        "detail": f"Error al procesar: {str(exc)}",
                    }
                )
            finally:
                try:
                    worker_db.close()
                except Exception:
                    pass
                events.put(None)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        while True:
            item = events.get()
            if item is None:
                break
            yield json.dumps(item, ensure_ascii=False) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
