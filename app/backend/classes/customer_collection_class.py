from sqlalchemy.orm import Session
from app.backend.db.models import DteModel, CollectionModel
from app.backend.classes.cashier_class import CashierClass
from sqlalchemy import func

class CustomerCollectionClass:
    def __init__(self, db: Session):
        self.db = db

    def store(self, form_data):
        period = form_data.period.split("-")
        year = int(period[0])
        month = int(period[1])
        period = f"{month:02d}-{year:04d}"
        date = form_data.period + "-01"

        results = (
            self.db.query(
                DteModel.branch_office_id,
                func.sum(DteModel.total).label("total_amount"),
                func.count(DteModel.id).label("total_tickets")
            )
            .filter(DteModel.period == period)
            .group_by(DteModel.branch_office_id)
            .all()
        )
        
        for result in results:
            branch_office_id = result.branch_office_id
            total_amount = int(result.total_amount)

            subscriber_cashier = CashierClass(self.db).get_subscriber_cashier(branch_office_id)
            
            check_existence = self.db.query(CollectionModel).filter(
                CollectionModel.branch_office_id == branch_office_id,
                CollectionModel.cashier_id == subscriber_cashier.id,
                CollectionModel.added_date == date
            ).count()
 
            if check_existence > 0:
                collection = self.db.query(CollectionModel).filter(
                    CollectionModel.branch_office_id == branch_office_id,
                    CollectionModel.cashier_id == subscriber_cashier.id,
                    CollectionModel.added_date == date
                ).first()

                collection.subscriber_amount = total_amount
                collection.total_tickets = result.total_tickets
                collection.updated_date = date
                self.db.commit()
                self.db.refresh(collection)
            else:
                collection = CollectionModel()
                collection.branch_office_id = branch_office_id
                collection.cashier_id = subscriber_cashier.id
                collection.subscriber_amount = total_amount
                collection.total_tickets = result.total_tickets
                collection.added_date = date
                collection.updated_date = date
                self.db.add(collection)
                self.db.commit()
                self.db.refresh(collection)


