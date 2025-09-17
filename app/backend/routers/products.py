from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.product_class import ProductClass
from app.backend.schemas import ProductRequest, CreateProduct, UpdateProduct, UserLogin
from app.backend.auth.auth_user import get_current_active_user
from typing import Optional

products = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@products.post("/")
def index(
    request: ProductRequest,
    session_user: UserLogin = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los productos con filtros y paginación
    """
    data = ProductClass(db).get_all(
        page=request.page,
        items_per_page=10,
        code=request.code,
        description=request.description
    )
    return {"message": data}

@products.post("/store")
def store(product: CreateProduct, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Crea un nuevo producto
    """
    data = ProductClass(db).store(product)
    return {"message": data}

@products.post("/create")
def create(product: CreateProduct, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Crea un nuevo producto (alias de store)
    """
    data = ProductClass(db).store(product)
    return {"message": data}

@products.get("/edit/{id}")
def edit(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtiene un producto específico por ID para edición
    """
    data = ProductClass(db).get("id", id)
    return {"message": data}

@products.delete("/delete/{id}")
def delete(id: int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Elimina un producto por ID
    """
    data = ProductClass(db).delete(id)
    return {"message": data}

@products.post("/update/")
def update(form_data: UpdateProduct, db: Session = Depends(get_db)):
    """
    Actualiza un producto existente
    """
    data = ProductClass(db).update(form_data)
    return {"message": data}

@products.put("/update/{id}")
def update_product(id: int, product: UpdateProduct, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Actualiza un producto existente mediante PUT con ID en URL
    """
    data = ProductClass(db).update(id, product)
    return {"message": data}

@products.get("/list")
def list(db: Session = Depends(get_db)):
    """
    Lista simple de productos
    """
    data = ProductClass(db).get_list()
    return {"message": data}