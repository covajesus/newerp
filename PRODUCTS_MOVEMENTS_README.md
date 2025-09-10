# Productos y Movimientos de Inventario - API Documentation

## Descripción
Se han agregado dos nuevos módulos al sistema ERP para la gestión de productos y movimientos de inventario:

- **Products**: Gestión de productos con stock, precios, proveedores, etc.
- **Movements**: Gestión de movimientos de entrada (IN) y salida (OUT) de productos

## Modelos de Base de Datos

### products
- `product_id` (int, primary key): ID único del producto
- `name` (varchar): Nombre del producto
- `description` (text): Descripción del producto
- `cost` (int): Costo del producto (en centavos)
- `price` (int): Precio de venta (en centavos)
- `stock` (int): Cantidad en stock
- `category_id` (int): ID de categoría (opcional)
- `supplier_id` (int): ID del proveedor (opcional)
- `brand` (varchar): Marca del producto
- `model` (varchar): Modelo del producto
- `barcode` (varchar): Código de barras (único)
- `status_id` (int): Estado del producto (1=activo, 0=inactivo)
- `created_at` (datetime): Fecha de creación
- `updated_at` (datetime): Fecha de última actualización

### movements
- `movement_id` (int, primary key): ID único del movimiento
- `movement_type` (varchar): Tipo de movimiento ('IN' o 'OUT')
- `reference_number` (varchar): Número de referencia (factura, orden, etc.)
- `description` (text): Descripción del movimiento
- `total_amount` (int): Monto total del movimiento
- `branch_office_id` (int): ID de la sucursal
- `supplier_id` (int): ID del proveedor (para entradas)
- `user_rut` (varchar): RUT del usuario que registra el movimiento
- `status_id` (int): Estado del movimiento (1=activo, 0=eliminado)
- `movement_date` (datetime): Fecha del movimiento
- `created_at` (datetime): Fecha de creación
- `updated_at` (datetime): Fecha de última actualización

### movements_products
- `movement_product_id` (int, primary key): ID único
- `product_id` (int, FK): ID del producto
- `movement_id` (int, FK): ID del movimiento
- `cost` (int): Costo unitario en el momento del movimiento
- `qty` (int): Cantidad (positiva para entradas, negativa para salidas)
- `created_at` (datetime): Fecha de creación
- `updated_at` (datetime): Fecha de última actualización

## Endpoints - Products

### Base URL: `/api/products`

#### GET `/api/products/`
Obtener todos los productos sin paginación
- **Response**: Lista de todos los productos activos

#### POST `/api/products/`
Obtener productos con paginación y filtros
- **Body**:
```json
{
  "page": 1,
  "items_per_page": 10,
  "search": "texto a buscar",
  "category_id": 1,
  "supplier_id": 2
}
```

#### POST `/api/products/store`
Crear un nuevo producto
- **Body**:
```json
{
  "name": "Nombre del producto",
  "description": "Descripción",
  "cost": 1000,
  "price": 1500,
  "stock": 100,
  "category_id": 1,
  "supplier_id": 2,
  "brand": "Marca",
  "model": "Modelo",
  "barcode": "1234567890123",
  "status_id": 1
}
```

#### GET `/api/products/{product_id}`
Obtener detalles de un producto específico

#### GET `/api/products/edit/{product_id}`
Obtener un producto para edición (mismo que el anterior)

#### PUT `/api/products/update/{product_id}`
Actualizar un producto existente
- **Body**: Misma estructura que store, pero todos los campos son opcionales

#### DELETE `/api/products/delete/{product_id}`
Eliminar un producto (cambia status_id a 0)

#### PUT `/api/products/update-stock/{product_id}?quantity={qty}&operation={add|subtract}`
Actualizar stock de un producto
- **Parameters**:
  - `quantity`: Cantidad a sumar o restar
  - `operation`: "add" para sumar, "subtract" para restar

## Endpoints - Movements

### Base URL: `/api/movements`

#### GET `/api/movements/`
Obtener todos los movimientos sin paginación

#### POST `/api/movements/`
Obtener movimientos con paginación y filtros
- **Body**:
```json
{
  "page": 1,
  "items_per_page": 10,
  "movement_type": "IN",
  "branch_office_id": 1,
  "supplier_id": 2,
  "date_from": "2024-01-01",
  "date_to": "2024-12-31"
}
```

#### POST `/api/movements/store`
Crear un nuevo movimiento
- **Body**:
```json
{
  "movement_type": "IN",
  "reference_number": "FAC-001",
  "description": "Compra de productos",
  "branch_office_id": 1,
  "supplier_id": 2,
  "user_rut": "12345678-9",
  "status_id": 1,
  "movement_date": "2024-01-15 10:30:00",
  "products": [
    {
      "product_id": 1,
      "cost": 1000,
      "qty": 50
    },
    {
      "product_id": 2,
      "cost": 2000,
      "qty": 25
    }
  ]
}
```

#### GET `/api/movements/{movement_id}`
Obtener detalles de un movimiento con sus productos

#### GET `/api/movements/edit/{movement_id}`
Obtener un movimiento para edición

#### PUT `/api/movements/update/{movement_id}`
Actualizar un movimiento existente
- **Body**: Campos del movimiento (sin productos)

#### DELETE `/api/movements/delete/{movement_id}`
Eliminar un movimiento y revertir cambios de stock

#### GET `/api/movements/{movement_id}/products`
Obtener solo los productos de un movimiento específico

#### GET `/api/movements/types/`
Obtener los tipos de movimiento disponibles

## Lógica de Negocio

### Gestión de Stock
- **Movimientos IN (Entrada)**: Suman al stock del producto
- **Movimientos OUT (Salida)**: Restan del stock del producto
- **Validaciones**: No permite sacar más stock del disponible
- **Reversión**: Al eliminar un movimiento, se revierten los cambios de stock

### Validaciones
1. **Productos**:
   - Código de barras único
   - Campos obligatorios: name, cost, price
   
2. **Movimientos**:
   - Tipo de movimiento válido (IN/OUT)
   - Usuario requerido (user_rut)
   - Al menos un producto por movimiento
   - Stock suficiente para salidas

### Estados
- `status_id = 1`: Activo
- `status_id = 0`: Eliminado/Inactivo

## Instalación

1. **Ejecutar el script SQL**:
```sql
-- Ejecutar el archivo create_products_movements_tables.sql
```

2. **Los archivos ya están creados**:
   - `app/backend/db/models.py` - Modelos agregados
   - `app/backend/classes/product_class.py` - Lógica de productos
   - `app/backend/classes/movement_class.py` - Lógica de movimientos
   - `app/backend/schemas.py` - Esquemas Pydantic agregados
   - `app/backend/routers/products.py` - Endpoints de productos
   - `app/backend/routers/movements.py` - Endpoints de movimientos
   - `main.py` - Routers registrados

3. **Reiniciar la aplicación** para que los cambios tomen efecto.

## Ejemplos de Uso

### Crear un producto
```bash
curl -X POST "http://localhost:8000/api/products/store" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Dell",
    "description": "Laptop para oficina",
    "cost": 50000,
    "price": 75000,
    "stock": 10,
    "brand": "Dell",
    "model": "Inspiron 15",
    "barcode": "DELL12345"
  }'
```

### Crear movimiento de entrada
```bash
curl -X POST "http://localhost:8000/api/movements/store" \
  -H "Content-Type: application/json" \
  -d '{
    "movement_type": "IN",
    "reference_number": "COMPRA-001",
    "description": "Compra inicial",
    "user_rut": "12345678-9",
    "movement_date": "2024-01-15 10:00:00",
    "products": [
      {
        "product_id": 1,
        "cost": 50000,
        "qty": 10
      }
    ]
  }'
```

### Listar productos
```bash
curl -X POST "http://localhost:8000/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "items_per_page": 10
  }'
```

## Notas Importantes

1. **Precios en centavos**: Todos los montos están en centavos para evitar problemas de decimales
2. **Transacciones**: Las operaciones de movimientos son transaccionales
3. **Autenticación**: Los endpoints pueden requerir autenticación según la configuración
4. **Logs**: Todas las operaciones quedan registradas con timestamps
5. **Relaciones**: Los productos pueden relacionarse con suppliers y categorías existentes
