from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Movement, UpdateMovement, MovementList, UserLogin
from app.backend.classes.movement_class import MovementClass
from app.backend.auth.auth_user import get_current_active_user

movements = APIRouter(
    prefix="/movements",
    tags=["Movements"]
)

@movements.post("/")
def index(movement_list: MovementList, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener lista de movimientos con paginación y filtros
    """
    try:
        data = MovementClass(db).get_all(
            page=movement_list.page,
            items_per_page=movement_list.items_per_page,
            type_id=movement_list.type_id,
            branch_office_id=movement_list.branch_office_id,
        )
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movements: {str(e)}")

@movements.post("/store")
def store(movement_inputs: Movement, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Crear un nuevo movimiento de inventario
    """
    try:
        data = MovementClass(db).store(movement_inputs)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating movement: {str(e)}")

@movements.post("/massive_upload")
def massive_upload(file: UploadFile = File(...), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Carga masiva de movimientos desde archivo Excel
    Columnas esperadas: sucursal, código, tipo de movimiento, cantidad, periodo
    """
    try:
        data = MovementClass(db).massive_upload(file, session_user.rut)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing massive upload: {str(e)}")

@movements.get("/edit/{movement_id}")
def edit(movement_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener un movimiento específico para edición
    """
    try:
        data = MovementClass(db).get(movement_id)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movement: {str(e)}")

@movements.put("/update/{movement_id}")
def update(movement_id: int, movement_inputs: UpdateMovement, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Actualizar un movimiento existente
    """
    try:
        data = MovementClass(db).update(movement_id, movement_inputs)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating movement: {str(e)}")

@movements.delete("/delete/{movement_id}")
def delete(movement_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Eliminar un movimiento (cambiar status a inactivo y revertir stock)
    """
    try:
        data = MovementClass(db).delete(movement_id)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting movement: {str(e)}")

@movements.get("/{movement_id}")
def show(movement_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener detalles de un movimiento específico con sus productos
    """
    try:
        data = MovementClass(db).get(movement_id)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movement: {str(e)}")

@movements.get("/{movement_id}/products")
def get_movement_products(movement_id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener los productos de un movimiento específico
    """
    try:
        data = MovementClass(db).get_movement_products(movement_id)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movement products: {str(e)}")

@movements.get("/list/all")
def get_all_movements(session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtener todos los movimientos sin paginación
    """
    try:
        data = MovementClass(db).get_all(page=0)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving movements: {str(e)}")

@movements.get("/types/list")
def get_movement_types(session_user: UserLogin = Depends(get_current_active_user)):
    """
    Obtener los tipos de movimiento disponibles
    """
    return {
        "message": {
            "status": "success",
            "data": [
                {"code": "IN", "name": "Entrada", "description": "Movimiento de entrada de productos"},
                {"code": "OUT", "name": "Salida", "description": "Movimiento de salida de productos"}
            ]
        }
    }

@movements.post("/impute/{movement_id}/{period}")
def impute_movement(movement_id: int, period: str, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Imputar un movimiento creando asientos contables en LibreDTE
    """
    try:
        data = MovementClass(db).impute(movement_id, period)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error imputing movement: {str(e)}")
