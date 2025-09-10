from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Movement, UpdateMovement, MovementList
from app.backend.classes.movement_class import MovementClass
from app.backend.auth.auth_user import get_current_active_user

class MovementsRouter:
    def __init__(self):
        self.router = APIRouter(
            prefix="/movements",
            tags=["Movements"]
        )
        self._add_routes()

    def _add_routes(self):
        self.router.post("/")(self.index)
        self.router.post("/store")(self.store)
        self.router.get("/edit/{movement_id}")(self.edit)
        self.router.put("/update/{movement_id}")(self.update)
        self.router.delete("/delete/{movement_id}")(self.delete)
        self.router.get("/{movement_id}")(self.show)
        self.router.get("/{movement_id}/products")(self.get_movement_products)
        self.router.get("/movement_products/{movement_id}")(self.movement_products)
        self.router.get("/")(self.get_all_movements)
        self.router.get("/types/")(self.get_movement_types)

    def index(self, movement_list: MovementList, db: Session = Depends(get_db)):
        """
        Obtener lista de movimientos con paginación y filtros
        """
        try:
            data = MovementClass(db).get_all(
                page=movement_list.page,
                items_per_page=movement_list.items_per_page,
                movement_type=movement_list.movement_type,
                branch_office_id=movement_list.branch_office_id,
                supplier_id=movement_list.supplier_id,
                date_from=movement_list.date_from,
                date_to=movement_list.date_to
            )
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving movements: {str(e)}")

    def store(self, movement_inputs: Movement, db: Session = Depends(get_db)):
        """
        Crear un nuevo movimiento de inventario
        """
        try:
            data = MovementClass(db).store(movement_inputs)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating movement: {str(e)}")

    def edit(self, movement_id: int, db: Session = Depends(get_db)):
        """
        Obtener un movimiento específico para edición
        """
        try:
            data = MovementClass(db).get(movement_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving movement: {str(e)}")

    def update(self, movement_id: int, movement_inputs: UpdateMovement, db: Session = Depends(get_db)):
        """
        Actualizar un movimiento existente
        """
        try:
            data = MovementClass(db).update(movement_id, movement_inputs)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating movement: {str(e)}")

    def delete(self, movement_id: int, db: Session = Depends(get_db)):
        """
        Eliminar un movimiento (cambiar status a inactivo y revertir stock)
        """
        try:
            data = MovementClass(db).delete(movement_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting movement: {str(e)}")

    def show(self, movement_id: int, db: Session = Depends(get_db)):
        """
        Obtener detalles de un movimiento específico con sus productos
        """
        try:
            data = MovementClass(db).get(movement_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving movement: {str(e)}")

    def get_movement_products(self, movement_id: int, db: Session = Depends(get_db)):
        """
        Obtener los productos de un movimiento específico
        """
        try:
            data = MovementClass(db).get_movement_products(movement_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving movement products: {str(e)}")

    def get_all_movements(self, db: Session = Depends(get_db)):
        """
        Obtener todos los movimientos sin paginación
        """
        try:
            data = MovementClass(db).get_all(page=0)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving movements: {str(e)}")

    def get_movement_types(self):
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

# Crear instancia del router
movements_router = MovementsRouter()
movements = movements_router.router
