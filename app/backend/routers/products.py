from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import Product, UpdateProduct, ProductList
from app.backend.classes.product_class import ProductClass
from app.backend.auth.auth_user import get_current_active_user

class ProductsRouter:
    def __init__(self):
        self.router = APIRouter(
            prefix="/products",
            tags=["Products"]
        )
        self._add_routes()

    def _add_routes(self):
        self.router.post("/")(self.index)
        self.router.post("/store")(self.store)
        self.router.get("/edit/{product_id}")(self.edit)
        self.router.put("/update/{product_id}")(self.update)
        self.router.delete("/delete/{product_id}")(self.delete)
        self.router.get("/{product_id}")(self.show)
        self.router.put("/update-stock/{product_id}")(self.update_stock)
        self.router.get("/")(self.get_all_products)

    def index(self, product_list: ProductList, db: Session = Depends(get_db)):
        """
        Obtener lista de productos con paginación y filtros
        """
        try:
            data = ProductClass(db).get_all(
                page=product_list.page,
                items_per_page=product_list.items_per_page,
                search=product_list.search,
                category_id=product_list.category_id,
                supplier_id=product_list.supplier_id
            )
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")

    def store(self, product_inputs: Product, db: Session = Depends(get_db)):
        """
        Crear un nuevo producto
        """
        try:
            data = ProductClass(db).store(product_inputs)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

    def edit(self, product_id: int, db: Session = Depends(get_db)):
        """
        Obtener un producto específico para edición
        """
        try:
            data = ProductClass(db).get(product_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")

    def update(self, product_id: int, product_inputs: UpdateProduct, db: Session = Depends(get_db)):
        """
        Actualizar un producto existente
        """
        try:
            data = ProductClass(db).update(product_id, product_inputs)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

    def delete(self, product_id: int, db: Session = Depends(get_db)):
        """
        Eliminar un producto (cambiar status a inactivo)
        """
        try:
            data = ProductClass(db).delete(product_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

    def show(self, product_id: int, db: Session = Depends(get_db)):
        """
        Obtener detalles de un producto específico
        """
        try:
            data = ProductClass(db).get(product_id)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")

    def update_stock(self, product_id: int, quantity: int, operation: str = "add", db: Session = Depends(get_db)):
        """
        Actualizar stock de un producto
        operation: 'add' para sumar, 'subtract' para restar
        """
        try:
            if operation not in ["add", "subtract"]:
                raise HTTPException(status_code=400, detail="Operation must be 'add' or 'subtract'")
            
            data = ProductClass(db).update_stock(product_id, quantity, operation)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating stock: {str(e)}")

    def get_all_products(self, db: Session = Depends(get_db)):
        """
        Obtener todos los productos sin paginación
        """
        try:
            data = ProductClass(db).get_all(page=0)
            return {"message": data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving products: {str(e)}")

# Crear instancia del router
products_router = ProductsRouter()
products = products_router.router
