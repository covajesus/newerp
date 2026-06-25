from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.classes.dte_line_item_name_class import DteLineItemNameClass
from app.backend.db.database import get_db
from app.backend.schemas import DteLineItemNameList, StoreDteLineItemName, UpdateDteLineItemName

dte_line_item_names = APIRouter(
    prefix="/dte_line_item_names",
    tags=["DteLineItemNames"],
)


@dte_line_item_names.post("/")
def index(form: DteLineItemNameList, db: Session = Depends(get_db)):
    data = DteLineItemNameClass(db).get_all(form.page, form.items_per_page)
    return {"message": data}


@dte_line_item_names.get("/list")
def list_all(db: Session = Depends(get_db)):
    data = DteLineItemNameClass(db).get_list()
    return {"message": data}


@dte_line_item_names.post("/store")
def store(form: StoreDteLineItemName, db: Session = Depends(get_db)):
    data = DteLineItemNameClass(db).store(form)
    return {"message": data}


@dte_line_item_names.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    DteLineItemNameClass(db).delete(id)
    return {"message": "success"}


@dte_line_item_names.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = DteLineItemNameClass(db).get(id)
    return {"message": data}


@dte_line_item_names.post("/update")
def update(form: UpdateDteLineItemName, db: Session = Depends(get_db)):
    data = DteLineItemNameClass(db).update(form)
    return {"message": data}
