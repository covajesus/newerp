from app.backend.db.models import MovementModel, MovementProductModel, ProductModel, BranchOfficeModel, SupplierModel, ProductCategoryModel, KardexValueModel
from app.backend.classes.product_class import ProductClass
from app.backend.classes.kardex_value_class import KardexValueClass
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from app.backend.classes.whatsapp_class import WhatsappClass
from datetime import datetime
import json
import pandas as pd
import io
import requests

class MovementClass:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, page=0, items_per_page=10, type_id=None, branch_office_id=None):
        """
        Obtiene todos los movimientos con paginación y filtros opcionales
        """
        try:
            filters = []
            
            if type_id:
                filters.append(MovementModel.type_id == type_id)
            
            if branch_office_id is not None:
                filters.append(MovementModel.branch_office_id == branch_office_id)

            query = self.db.query(
                MovementModel.id,
                MovementModel.type_id,
                MovementModel.branch_office_id,
                MovementModel.status_id,
                func.date_format(MovementModel.added_date, "%d-%m-%Y %H:%i:%s").label("added_date"),
                BranchOfficeModel.branch_office.label("branch_office_name")
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == MovementModel.branch_office_id
            ).filter(
                *filters
            ).order_by(
                MovementModel.id.desc()
            )

            if page > 0:
                total_items = query.count()
                total_pages = (total_items + items_per_page - 1) // items_per_page

                if page < 1 or page > total_pages:
                    return {"status": "error", "message": "Invalid page number"}

                data = query.offset((page - 1) * items_per_page).limit(items_per_page).all()

                if not data:
                    return {"status": "error", "message": "No data found"}

                serialized_data = [{
                    "id": movement.id,
                    "type_id": movement.type_id,
                    "branch_office_id": movement.branch_office_id,
                    "branch_office_name": movement.branch_office_name,
                    "status_id": movement.status_id,
                    "added_date": movement.added_date
                } for movement in data]

                return {
                    "status": "success",
                    "data": serialized_data,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "current_page": page
                }
            else:
                data = query.all()
                
                serialized_data = [{
                    "id": movement.id,
                    "type_id": movement.type_id,
                    "branch_office_id": movement.branch_office_id,
                    "branch_office_name": movement.branch_office_name,
                    "status_id": movement.status_id,
                    "added_date": movement.added_date
                } for movement in data]

                return serialized_data

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movements: {str(e)}"}

    def get(self, movement_id):
        """
        Obtiene un movimiento específico con sus productos
        """
        try:
            # Obtener datos del movimiento
            movement_query = self.db.query(
                MovementModel.id,
                MovementModel.type_id,
                MovementModel.description,
                MovementModel.total_amount,
                MovementModel.branch_office_id,
                MovementModel.supplier_id,
                MovementModel.user_rut,
                MovementModel.status_id,
                func.date_format(MovementModel.movement_date, "%d-%m-%Y %H:%i:%s").label("movement_date"),
                func.date_format(MovementModel.added_date, "%d-%m-%Y %H:%i:%s").label("added_date"),
                BranchOfficeModel.branch_office.label("branch_office_name"),
                SupplierModel.supplier.label("supplier_name")
            ).outerjoin(
                BranchOfficeModel, BranchOfficeModel.id == MovementModel.branch_office_id
            ).outerjoin(
                SupplierModel, SupplierModel.id == MovementModel.supplier_id
            ).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement_query:
                return {"status": "error", "message": "Movement not found"}

            # Obtener productos del movimiento
            products_query = self.db.query(
                MovementProductModel.movement_product_id,
                MovementProductModel.product_id,
                MovementProductModel.cost,
                MovementProductModel.qty,
                ProductModel.name.label("product_name"),
                ProductModel.description.label("product_description"),
                ProductModel.barcode.label("product_barcode")
            ).join(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_id == movement_id
            ).all()

            movement_data = {
                "movement_id": movement_query.movement_id,
                "movement_type": movement_query.movement_type,
                "description": movement_query.description,
                "total_amount": movement_query.total_amount,
                "branch_office_id": movement_query.branch_office_id,
                "branch_office_name": movement_query.branch_office_name,
                "supplier_id": movement_query.supplier_id,
                "supplier_name": movement_query.supplier_name,
                "user_rut": movement_query.user_rut,
                "status_id": movement_query.status_id,
                "movement_date": movement_query.movement_date,
                "added_date": movement_query.added_date,
                "products": [{
                    "movement_product_id": product.movement_product_id,
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "product_description": product.product_description,
                    "product_barcode": product.product_barcode,
                    "cost": product.cost,
                    "qty": product.qty,
                    "subtotal": product.cost * product.qty
                } for product in products_query]
            }

            return {"status": "success", "data": movement_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement: {str(e)}"}

    def store(self, form_data):
        """
        Crear un nuevo movimiento con productos
        """
        try:
            # Crear movimiento
            new_movement = MovementModel(
                type_id=form_data.type_id,
                branch_office_id=form_data.branch_office_id,
                status_id=17,
                added_date=datetime.utcnow(),
                updated_date=datetime.utcnow()
            )

            self.db.add(new_movement)
            self.db.commit()
            self.db.refresh(new_movement)

            # Crear productos del movimiento y actualizar stock            
            # Crear productos del movimiento y actualizar stock
            product_class = ProductClass(self.db)
            kardex_class = KardexValueClass(self.db)
            
            for product_data in form_data.products:
                # Determinar la cantidad según el tipo de movimiento
                # type_id 2 y 4 = Salidas (cantidad negativa)
                # type_id 1 y 3 = Entradas (cantidad positiva)
                if form_data.type_id in [2, 4]:
                    qty_to_save = -abs(product_data.quantity)  # Asegurar que sea negativo
                    qty_for_kardex = -product_data.quantity    # Cantidad negativa para kardex
                else:
                    qty_to_save = abs(product_data.quantity)   # Asegurar que sea positivo
                    qty_for_kardex = product_data.quantity     # Cantidad positiva para kardex
                
                # Crear registro en movements_products
                movement_product = MovementProductModel(
                    product_id=product_data.product_id,
                    movement_id=new_movement.id,
                    qty=qty_to_save,
                    cost=product_data.cost,
                    added_date=datetime.utcnow(),
                    updated_date=datetime.utcnow()
                )
                
                self.db.add(movement_product)
                
                # Actualizar stock según el tipo de movimiento
                # type_id 1, 3 = Entrada (add), type_id 2, 4 = Salida (subtract)
                if form_data.type_id in [1, 3]:
                    # Entrada: sumar al stock
                    stock_result = product_class.update_stock(product_data.product_id, product_data.quantity, "add")
                elif form_data.type_id in [2, 4]:
                    # Salida: restar del stock
                    stock_result = product_class.update_stock(product_data.product_id, product_data.quantity, "subtract")
                    if stock_result and isinstance(stock_result, dict) and stock_result.get("status") == "error":
                        self.db.rollback()
                        return stock_result
                
                # Registrar en kardex_values con costo promedio ponderado
                kardex_result = kardex_class.store_kardex_entry(
                    product_id=product_data.product_id,
                    qty_change=qty_for_kardex,
                    new_cost=product_data.cost
                )
                
                if kardex_result and isinstance(kardex_result, dict) and kardex_result.get("status") == "error":
                    self.db.rollback()
                    return kardex_result
                
                # Crear asiento contable para salidas (type_id == 2)
                if form_data.type_id == 2:
                    try:
                        if form_data.alert_id == 1:
                            # Enviar notificación por WhatsApp
                            whatsapp_class = WhatsappClass(self.db)
                            whatsapp_class.movements(new_movement.id)

                        # Obtener datos necesarios para el asiento
                        product = self.db.query(ProductModel).filter(ProductModel.id == product_data.product_id).first()
                        branch_office = self.db.query(BranchOfficeModel).filter(BranchOfficeModel.id == form_data.branch_office_id).first()
                        product_category = self.db.query(ProductCategoryModel).filter(ProductCategoryModel.id == product.product_category_id).first()
                        
                        if product_category and product_category.accounting_account:
                            accounting_account = str(product_category.accounting_account).strip()
                            
                            # Obtener el costo del kardex actualizado
                            kardex_value = self.db.query(KardexValueModel).filter(KardexValueModel.product_id == product_data.product_id).first()
                            cost_to_use = kardex_value.cost if kardex_value else product_data.cost
                            
                            # Preparar fecha para asiento (primer día del mes actual)
                            now = datetime.now()
                            day = "01"
                            month = f"{now.month:02d}"
                            year = str(now.year)
                            utf8_date = f"{day}-{month}-{year}"
                            
                            # Preparar datos del asiento
                            message = f"{branch_office.branch_office}_{accounting_account}_{utf8_date}_SalidaInventario_{new_movement.id}_{movement_product.id}"
                            
                            url = 'https://libredte.cl'
                            hash_value = 'JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1'
                            emisor = '76063822-6'
                            
                            amount = round(cost_to_use * product_data.quantity)
                            
                            datos = {
                                'fecha': f"{year}-{month}-{day}",
                                'glosa': message,
                                'detalle': {
                                    'debe': {
                                        accounting_account: amount
                                    },
                                    'haber': {
                                        '111000102': amount
                                    }
                                },
                                'operacion': 'I',
                                'documentos': {
                                    'emitidos': [{'dte': '', 'folio': new_movement.id}]
                                }
                            }
                            
                            # Realizar petición a LibreDTE
                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': f'Bearer {hash_value}'
                            }
                            
                            response = requests.post(
                                f"{url}/lce/lce_asientos/crear/{emisor}",
                                json=datos,
                                headers=headers,
                                timeout=30
                            )
                            
                            if response.status_code != 200:
                                # Log del error pero no fallar la operación
                                print(f"Error al crear asiento contable: {response.text}")
                            
                    except Exception as e:
                        # Log del error pero no fallar la operación principal
                        print(f"Error en creación de asiento contable: {str(e)}")
                        # No hacer rollback por errores de asiento contable

            self.db.commit()

            return {"status": "success", "message": "Movement created successfully", "movement_id": new_movement.id}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error creating movement: {str(e)}"}

    def update(self, movement_id, form_data):
        """
        Actualizar un movimiento existente
        """
        try:
            movement = self.db.query(MovementModel).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement:
                return {"status": "error", "message": "Movement not found"}

            # Actualizar campos del movimiento
            if form_data.movement_type is not None:
                movement.movement_type = form_data.movement_type
            if form_data.description is not None:
                movement.description = form_data.description
            if form_data.branch_office_id is not None:
                movement.branch_office_id = form_data.branch_office_id
            if form_data.supplier_id is not None:
                movement.supplier_id = form_data.supplier_id
            if form_data.user_rut is not None:
                movement.user_rut = form_data.user_rut
            if form_data.status_id is not None:
                movement.status_id = form_data.status_id
            if form_data.movement_date is not None:
                movement.movement_date = datetime.strptime(form_data.movement_date, "%Y-%m-%d %H:%M:%S")

            movement.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Movement updated successfully"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error updating movement: {str(e)}"}

    def delete(self, movement_id):
        """
        Eliminar un movimiento (cambiar status_id a 0) y revertir cambios de stock
        """
        try:
            movement = self.db.query(MovementModel).filter(
                MovementModel.movement_id == movement_id
            ).first()

            if not movement:
                return {"status": "error", "message": "Movement not found"}

            # Obtener productos del movimiento para revertir stock
            movement_products = self.db.query(MovementProductModel).filter(
                MovementProductModel.movement_id == movement_id
            ).all()

            product_class = ProductClass(self.db)
            
            # Revertir cambios de stock
            for movement_product in movement_products:
                if movement.movement_type == "IN":
                    # Si fue entrada, restar del stock
                    product_class.update_stock(movement_product.product_id, movement_product.qty, "subtract")
                elif movement.movement_type == "OUT":
                    # Si fue salida, sumar al stock
                    product_class.update_stock(movement_product.product_id, movement_product.qty, "add")

            # Marcar movimiento como eliminado
            movement.status_id = 0
            movement.updated_at = datetime.utcnow()

            self.db.commit()

            return {"status": "success", "message": "Movement deleted successfully and stock reverted"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error deleting movement: {str(e)}"}

    def get_movement_products(self, movement_id):
        """
        Obtiene los productos de un movimiento específico
        """
        try:
            products_query = self.db.query(
                MovementProductModel.movement_product_id,
                MovementProductModel.product_id,
                MovementProductModel.cost,
                MovementProductModel.qty,
                ProductModel.name.label("product_name"),
                ProductModel.description.label("product_description"),
                ProductModel.barcode.label("product_barcode"),
                ProductModel.stock.label("current_stock")
            ).join(
                ProductModel, ProductModel.product_id == MovementProductModel.product_id
            ).filter(
                MovementProductModel.movement_id == movement_id
            ).all()

            if not products_query:
                return {"status": "error", "message": "No products found for this movement"}

            products_data = [{
                "movement_product_id": product.movement_product_id,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "product_description": product.product_description,
                "product_barcode": product.product_barcode,
                "cost": product.cost,
                "qty": product.qty,
                "subtotal": product.cost * product.qty,
                "current_stock": product.current_stock
            } for product in products_query]

            return {"status": "success", "data": products_data}

        except Exception as e:
            return {"status": "error", "message": f"Error retrieving movement products: {str(e)}"}

    def massive_upload(self, file, user_rut):
        """
        Carga masiva de movimientos desde archivo Excel
        Columnas esperadas: sucursal, codigo, tipo de movimiento, cantidad, periodo
        """
        try:
            # Verificar que el archivo sea Excel
            if not file.filename.endswith(('.xlsx', '.xls')):
                return {"status": "error", "message": "File must be an Excel file (.xlsx or .xls)"}
            
            # Leer el archivo Excel
            contents = file.file.read()
            df = pd.read_excel(io.BytesIO(contents))
            
            # Validar columnas requeridas
            required_columns = ['sucursal', 'codigo', 'tipo de movimiento', 'cantidad', 'periodo']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {"status": "error", "message": f"Missing required columns: {', '.join(missing_columns)}"}
            
            # Estadísticas de procesamiento
            total_rows = len(df)
            processed_rows = 0
            error_rows = []
            
            # Procesar cada fila
            for index, row in df.iterrows():
                try:
                    # Obtener datos de la fila
                    branch_office = row['sucursal']
                    product_code = str(row['codigo']).strip()
                    movement_type = int(row['tipo de movimiento'])
                    quantity = int(row['cantidad'])
                    period = str(row['periodo']).strip()
                    
                    # Buscar sucursal por nombre
                    branch_office = self.db.query(BranchOfficeModel).filter(
                        BranchOfficeModel.id == branch_office
                    ).first()
                    
                    if not branch_office:
                        error_rows.append(f"Row {index + 2}: Branch office '{branch_office}' not found")
                        continue
                    
                    # Buscar producto por codigo
                    product = self.db.query(ProductModel).filter(
                        ProductModel.id == product_code
                    ).first()
                    
                    if not product:
                        error_rows.append(f"Row {index + 2}: Product with code '{product_code}' not found")
                        continue
                    
                    # Validar tipo de movimiento (1=Entrada, 2=Salida, 3=Ajuste+, 4=Ajuste-)
                    if movement_type not in [1, 2, 3, 4]:
                        error_rows.append(f"Row {index + 2}: Invalid movement type '{movement_type}'. Must be 1, 2, 3, or 4")
                        continue
                    
                    # Validar cantidad
                    if quantity <= 0:
                        error_rows.append(f"Row {index + 2}: Quantity must be greater than 0")
                        continue
                    
                    # Crear movimiento individual para cada producto
                    new_movement = MovementModel(
                        type_id=movement_type,
                        branch_office_id=branch_office.id,
                        status_id=17,
                        document_number=0,
                        added_date=datetime.utcnow(),
                        updated_date=datetime.utcnow()
                    )
                    
                    self.db.add(new_movement)
                    self.db.flush()  # Para obtener el ID sin hacer commit
                    
                    # Determinar cantidad para BD y kardex
                    if movement_type in [2, 4]:  # Salidas
                        qty_to_save = -abs(quantity)
                        qty_for_kardex = -quantity
                    else:  # Entradas
                        qty_to_save = abs(quantity)
                        qty_for_kardex = quantity
                    
                    # Crear registro de producto del movimiento
                    movement_product = MovementProductModel(
                        product_id=product.id,
                        movement_id=new_movement.id,
                        qty=qty_to_save,
                        cost=0,  # Costo 0 para carga masiva, se puede ajustar después
                        added_date=datetime.utcnow(),
                        updated_date=datetime.utcnow()
                    )
                    
                    self.db.add(movement_product)
                    
                    # Actualizar stock
                    product_class = ProductClass(self.db)
                    if movement_type in [1, 3]:  # Entradas
                        stock_result = product_class.update_stock(product.id, quantity, "add")
                    else:  # Salidas
                        stock_result = product_class.update_stock(product.id, quantity, "subtract")
                        if stock_result and isinstance(stock_result, dict) and stock_result.get("status") == "error":
                            error_rows.append(f"Row {index + 2}: {stock_result.get('message')}")
                            continue
                    
                    # Registrar en kardex
                    kardex_class = KardexValueClass(self.db)
                    kardex_result = kardex_class.store_kardex_entry(
                        product_id=product.id,
                        qty_change=qty_for_kardex,
                        new_cost=0  # Costo 0 para carga masiva
                    )
                    
                    if kardex_result and isinstance(kardex_result, dict) and kardex_result.get("status") == "error":
                        error_rows.append(f"Row {index + 2}: Kardex error - {kardex_result.get('message')}")
                        continue
                    
                    # Imputar automáticamente solo si es un movimiento de salida (tipo 2)
                    if movement_type == 2:
                        try:
                            # Obtener la categoría del producto para la cuenta contable
                            category = self.db.query(ProductCategoryModel).filter(
                                ProductCategoryModel.id == product.product_category_id
                            ).first()
                            
                            if category and category.accounting_account:
                                # Configuración de LibreDTE
                                TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
                                url_base = "https://libredte.cl"
                                emisor = "76063822"
                                
                                # Obtener el costo del kardex para el cálculo
                                kardex_value = self.db.query(KardexValueModel).filter(
                                    KardexValueModel.product_id == product.id
                                ).first()
                                
                                # Usar el costo del kardex o un valor por defecto
                                cost_to_use = kardex_value.cost if kardex_value and kardex_value.cost else 100  # Valor por defecto para carga masiva
                                
                                # Procesar fecha usando el período del Excel
                                try:
                                    year_str, month_str = period.split('-')
                                    year = int(year_str)
                                    month = int(month_str)
                                    
                                    # Obtener día actual para lógica del día 25
                                    current_day = datetime.now().day
                                    
                                    # Si estamos después del día 25, usar el mes siguiente
                                    if current_day > 25:
                                        month += 1
                                        if month > 12:
                                            month = 1
                                            year += 1
                                    
                                    # Formatear fecha para LibreDTE (YYYY-MM-DD)
                                    fecha_libredte = f"{year}-{month:02d}-01"
                                    
                                    # Formatear fecha para mensaje (DD-MM-YYYY)
                                    fecha_mensaje = f"01-{month:02d}-{year}"
                                    
                                    # Crear mensaje/glosa
                                    accounting_account = str(category.accounting_account).strip()
                                    message = f"{branch_office.branch_office}_{accounting_account}_{fecha_mensaje}_SalidaInventario_Masiva_{new_movement.id}_{movement_product.id}"
                                    
                                    # Calcular montos
                                    total_amount = round(cost_to_use * quantity)
                                    
                                    # Crear datos para LibreDTE
                                    datos = {
                                        "fecha": fecha_libredte,
                                        "glosa": message,
                                        "detalle": {
                                            "debe": {
                                                accounting_account: total_amount  # Cuenta de gasto/costo
                                            },
                                            "haber": {
                                                "111000102": total_amount  # Cuenta de inventario
                                            }
                                        },
                                        "operacion": "I",
                                        "documentos": {
                                            "emitidos": [
                                                {
                                                    "dte": "",
                                                    "folio": str(new_movement.id)
                                                }
                                            ]
                                        }
                                    }
                                    
                                    # Enviar a LibreDTE
                                    url_create = f"{url_base}/api/lce/lce_asientos/crear/{emisor}"
                                    
                                    response = requests.post(
                                        url_create,
                                        json=datos,
                                        headers={
                                            "Authorization": f"Bearer {TOKEN}",
                                            "Content-Type": "application/json"
                                        }
                                    )
                                    
                                    # Si la imputación es exitosa, actualizar status del movimiento
                                    if response.status_code == 200:
                                        new_movement.status_id = 15  # Imputado
                                    else:
                                        print(f"Warning: Failed to create accounting entry for movement {new_movement.id}: {response.text}")
                                        
                                except Exception as date_error:
                                    print(f"Error processing period {period} for movement {new_movement.id}: {str(date_error)}")
                                    
                        except Exception as impute_error:
                            print(f"Error creating accounting entry for movement {new_movement.id}: {str(impute_error)}")
                            # No agregar a error_rows para no fallar el procesamiento del movimiento
                    
                    processed_rows += 1
                    
                except Exception as e:
                    error_rows.append(f"Row {index + 2}: Error processing row - {str(e)}")
                    continue
            
            # Commit todos los cambios si no hay errores críticos
            if processed_rows > 0:
                self.db.commit()
            else:
                self.db.rollback()
            
            return {
                "status": "success" if processed_rows > 0 else "error",
                "message": f"Processed {processed_rows} of {total_rows} rows",
                "details": {
                    "total_rows": total_rows,
                    "processed_rows": processed_rows,
                    "error_rows": len(error_rows),
                    "errors": error_rows[:10] if error_rows else []  # Mostrar solo los primeros 10 errores
                }
            }
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error processing Excel file: {str(e)}"}

    def impute(self, movement_id, period):
        """
        Imputa un movimiento creando asientos contables en LibreDTE
        Actualiza el status_id del movimiento y crea asientos contables para cada producto
        """
        try:
            # Buscar el movimiento
            movement = self.db.query(MovementModel).filter(MovementModel.id == movement_id).first()
            if not movement:
                return {"status": "error", "message": "Movement not found"}
            
            # Actualizar el status_id del movimiento (manteniendo el patrón del sistema)
            movement.status_id = 15  # Asumiendo que 15 es "imputado" como en honorary_class
            movement.updated_date = datetime.now()
            
            # Obtener los productos del movimiento
            movement_products = self.db.query(MovementProductModel).filter(
                MovementProductModel.movement_id == movement_id
            ).all()
            
            if not movement_products:
                return {"status": "error", "message": "No products found for this movement"}
            
            # Configuración de LibreDTE
            TOKEN = "JXou3uyrc7sNnP2ewOCX38tWZ6BTm4D1"
            url_base = "https://libredte.cl"
            emisor = "76063822"
            
            # Procesar cada producto del movimiento
            for movement_product in movement_products:
                try:
                    # Calcular el PMP (Precio Medio Ponderado) para el producto
                    pmp_result = self.db.query(
                        KardexValueModel.cost.label('pmp')
                    ).join(
                        ProductModel, ProductModel.id == KardexValueModel.product_id
                    ).filter(
                        ProductModel.id == movement_product.product_id
                    ).first()
                    
                    pmp = round(pmp_result.pmp) if pmp_result.pmp else 0
                    
                    # Obtener detalles del producto y categoría
                    product = self.db.query(ProductModel).filter(
                        ProductModel.id == movement_product.product_id
                    ).first()
                    
                    if not product:
                        continue
                    
                    category = self.db.query(ProductCategoryModel).filter(
                        ProductCategoryModel.id == product.product_category_id
                    ).first()
                    
                    if not category or not category.accounting_account:
                        continue
                    
                    # Obtener sucursal
                    branch_office = self.db.query(BranchOfficeModel).filter(
                        BranchOfficeModel.id == movement.branch_office_id
                    ).first()
                    
                    branch_office_name = branch_office.branch_office if branch_office else "Unknown"
                    accounting_account = category.accounting_account.strip()
                    
                    # Procesar fecha usando el período proporcionado
                    try:
                        # Usar el período proporcionado (formato YYYY-MM)
                        year_str, month_str = period.split('-')
                        year = int(year_str)
                        month = int(month_str)
                        
                        # Obtener día actual para lógica del día 25
                        current_day = datetime.now().day
                        
                        # Si estamos después del día 25, usar el mes siguiente
                        if current_day > 25:
                            month += 1
                            if month > 12:
                                month = 1
                                year += 1
                        
                        # Formatear mes con cero inicial si es necesario
                        month_str = f"{month:02d}"
                        
                        # Formatear fecha para LibreDTE (YYYY-MM-DD)
                        fecha_libredte = f"{year}-{month_str}-01"
                        
                        # Formatear fecha para mensaje (DD-MM-YYYY)
                        fecha_mensaje = f"01-{month_str}-{year}"
                        
                    except Exception as date_error:
                        return {"status": "error", "message": f"Error processing period {period}: {str(date_error)}"}
                    
                    # Crear mensaje/glosa
                    message = f"{branch_office_name}_{accounting_account}_{fecha_mensaje}_SalidaInventario_{movement.id}_{movement_product.id}"
                    
                    # Calcular montos
                    qty = abs(movement_product.qty)
                    total_amount = round(pmp * qty)
                    
                    # Crear datos para LibreDTE
                    datos = {
                        "fecha": fecha_libredte,
                        "glosa": message,
                        "detalle": {
                            "debe": {
                                str(accounting_account): total_amount  # Cuenta de gasto/costo como string
                            },
                            "haber": {
                                "111000102": total_amount  # Cuenta de inventario
                            }
                        },
                        "operacion": "I",
                        "documentos": {
                            "emitidos": [
                                {
                                    "dte": "",
                                    "folio": str(movement.document_number) if movement.document_number else ""
                                }
                            ]
                        }
                    }
                    
                    # Enviar a LibreDTE
                    url_create = f"{url_base}/api/lce/lce_asientos/crear/{emisor}"
                    
                    response = requests.post(
                        url_create,
                        json=datos,
                        headers={
                            "Authorization": f"Bearer {TOKEN}",
                            "Content-Type": "application/json"
                        }
                    )
                    
                    print(f"LibreDTE Response for product {movement_product.id}: {response.text}")
                    
                    # Verificar respuesta siguiendo el patrón de otras clases
                    if response.status_code != 200:
                        print(f"Warning: Failed to create accounting entry for product {movement_product.id}: {response.text}")
                        # Continuar con el siguiente producto
                        continue
                        
                except Exception as product_error:
                    print(f"Error processing product {movement_product.id}: {str(product_error)}")
                    # Continuar con el siguiente producto
                    continue
            
            # Guardar cambios en el movimiento
            self.db.commit()
            
            return {
                "status": "success", 
                "message": "Movement imputed successfully. Accounting entries created."
            }
            
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error imputing movement: {str(e)}"}
