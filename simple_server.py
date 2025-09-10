from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/test-kardex")
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

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
