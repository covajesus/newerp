from fastapi import APIRouter, Depends
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.backend.classes.expense_type_class import ExpenseTypeClass
from app.backend.schemas import ExpenseType, StoreExpenseType, UpdateExpenseType
from app.backend.db.models import ExpenseTypeModel

expense_types = APIRouter(
    prefix="/expense_types",
    tags=["ExpenseTypes"]
)

@expense_types.post("/")
def index(expense_type_inputs: ExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_list(expense_type_inputs.page)

    return {"message": data}

@expense_types.get("/")
def index(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all()

    return {"message": data}

@expense_types.get("/list")
def list(db: Session = Depends(get_db)):
    """
    Lista simple de expense types
    """
    data = ExpenseTypeClass(db).get_all()
    return {"message": data}

@expense_types.get("/capitulation_visibles")
def capitulation_visibles(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all_capitulation_visibles()

    return {"message": data}

@expense_types.get("/eerr_visibles")
def eerr_visibles(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all_eerr_visibles()

    return {"message": data}

@expense_types.get("/track_visibles")
def track_visibles(db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get_all_track_visibles()

    return {"message": data}

@expense_types.post("/store")
def store(expense_type_inputs: StoreExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).store(expense_type_inputs)
    return {"message": data}

@expense_types.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    ExpenseTypeClass(db).delete(id)

    return {"message": "success"}

@expense_types.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).get(id)

    return {"message": data}

@expense_types.post("/update")
def post(update_expense_type: UpdateExpenseType, db: Session = Depends(get_db)):
    data = ExpenseTypeClass(db).update(update_expense_type)

    return {"message": data}

@expense_types.get("/external_data")
def get_external_data(db: Session = Depends(get_db)):
    """
    Actualiza positive_negative_id en expense_types basado en coincidencias de accounting_account con expense_types2
    """
    try:
        # Query para obtener datos de la tabla expense_types (principal)
        query_db1 = text("""
            SELECT 
                id,
                accounting_account,
                expense_type
            FROM expense_types
        """)
        
        # Query para obtener datos de la tabla expense_types2 (con positive_negative_id)
        query_db2 = text("""
            SELECT 
                expense_type_id,
                accounting_account,
                expense_type,
                positive_negative_id
            FROM expense_types2
        """)
        
        # Ejecutar consultas en la misma base de datos
        result_db1 = db.execute(query_db1)
        result_db2 = db.execute(query_db2)
        
        # Convertir resultados a diccionarios con accounting_account como clave
        data_db1 = {}
        for row in result_db1:
            data_db1[str(row.accounting_account)] = {
                "id": row.id,
                "accounting_account": str(row.accounting_account),
                "expense_type": row.expense_type
            }
        
        data_db2 = {}
        for row in result_db2:
            data_db2[str(row.accounting_account)] = {
                "id": row.expense_type_id,
                "accounting_account": str(row.accounting_account),
                "expense_type": row.expense_type,
                "positive_negative_id": row.positive_negative_id
            }
        
        # Encontrar coincidencias y realizar updates
        updates_made = []
        matching_accounts = []
        
        for accounting_account in data_db1.keys():
            if accounting_account in data_db2:
                matching_accounts.append(accounting_account)
                
                # Obtener el registro de la tabla expense_types (principal)
                expense_type_record = db.query(ExpenseTypeModel).filter(
                    ExpenseTypeModel.accounting_account == accounting_account
                ).first()
                
                if expense_type_record:
                    # Actualizar el positive_negative_id con el valor de expense_types2
                    old_value = getattr(expense_type_record, 'positive_negative_id', None)
                    new_value = data_db2[accounting_account]["positive_negative_id"]
                    
                    # Solo crear el campo si no existe en el modelo actual
                    if hasattr(expense_type_record, 'positive_negative_id'):
                        expense_type_record.positive_negative_id = new_value
                    else:
                        # Si el campo no existe en el modelo, usar SQL directo
                        update_query = text("""
                            UPDATE expense_types 
                            SET positive_negative_id = :new_value 
                            WHERE accounting_account = :account
                        """)
                        db.execute(update_query, {
                            "new_value": new_value,
                            "account": accounting_account
                        })
                    
                    updates_made.append({
                        "id": expense_type_record.id,
                        "accounting_account": accounting_account,
                        "old_positive_negative_id": old_value,
                        "new_positive_negative_id": new_value
                    })
        
        # Si hay coincidencias, confirmar cambios
        if matching_accounts:
            db.commit()  # Confirmar los cambios en la base de datos
        
        # Preparar respuesta
        result = {
            "total_matching_accounts": len(matching_accounts),
            "matching_accounts": matching_accounts,
            "updates_made": updates_made,
            "total_updates": len(updates_made)
        }
        
        return {"message": result}
        
    except Exception as e:
        db.rollback()  # Revertir cambios en caso de error
        return {"error": f"Error al actualizar las bases de datos: {str(e)}"}
