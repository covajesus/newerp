from fastapi import APIRouter

test_router = APIRouter(
    prefix="/test",
    tags=["Test"]
)

@test_router.get("/")
async def test_endpoint():
    return {"message": "Test endpoint working"}

@test_router.post("/kardex-simple")
async def test_kardex():
    return {
        "message": {
            "data": [
                {
                    "code": "TEST001",
                    "description": "Producto de prueba 1", 
                    "min_stock": 10.0,
                    "max_stock": 100.0,
                    "balance": 50.0,
                    "pmp": 25.50,
                    "stock_status": "normal"
                }
            ],
            "total_items": 1,
            "items_per_page": 10,
            "current_page": 1
        }
    }

@test_router.get("/database-check")
async def check_database():
    from app.backend.db.database import SessionLocal
    from app.backend.db.models import ProductModel, MovementModel, KardexValueModel
    
    with SessionLocal() as session:
        try:
            product_count = session.query(ProductModel).count()
            movement_count = session.query(MovementModel).count()
            kardex_count = session.query(KardexValueModel).count()
            
            # Obtener algunos productos de ejemplo
            sample_products = session.query(ProductModel).limit(5).all()
            
            return {
                "database_status": "connected",
                "table_counts": {
                    "products": product_count,
                    "movements": movement_count,
                    "kardex_values": kardex_count
                },
                "sample_products": [
                    {
                        "id": p.product_id,
                        "name": p.name,
                        "description": p.description,
                        "stock": p.stock,
                        "barcode": p.barcode
                    } for p in sample_products
                ]
            }
        except Exception as e:
            return {
                "database_status": "error",
                "error": str(e)
            }
