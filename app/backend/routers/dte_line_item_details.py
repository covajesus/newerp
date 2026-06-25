from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.classes.dte_line_item_detail_class import DteLineItemDetailClass
from app.backend.db.database import get_db
from app.backend.schemas import (
    DteLineItemDetailList,
    StoreDteLineItemDetail,
    UpdateDteLineItemDetail,
)

dte_line_item_details = APIRouter(
    prefix="/dte_line_item_details",
    tags=["DteLineItemDetails"],
)


@dte_line_item_details.post("/")
def index(form: DteLineItemDetailList, db: Session = Depends(get_db)):
    data = DteLineItemDetailClass(db).get_all(form.page, form.items_per_page)
    return {"message": data}


@dte_line_item_details.get("/list")
def list_all(db: Session = Depends(get_db)):
    data = DteLineItemDetailClass(db).get_list()
    return {"message": data}


@dte_line_item_details.post("/store")
def store(form: StoreDteLineItemDetail, db: Session = Depends(get_db)):
    data = DteLineItemDetailClass(db).store(form)
    return {"message": data}


@dte_line_item_details.delete("/delete/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    DteLineItemDetailClass(db).delete(id)
    return {"message": "success"}


@dte_line_item_details.get("/edit/{id}")
def edit(id: int, db: Session = Depends(get_db)):
    data = DteLineItemDetailClass(db).get(id)
    return {"message": data}


@dte_line_item_details.post("/update")
def update(form: UpdateDteLineItemDetail, db: Session = Depends(get_db)):
    data = DteLineItemDetailClass(db).update(form)
    return {"message": data}
