from app.backend.db.models import HrFinalDayMonthModel

class HrFinalDayMonthClass:
    def __init__(self, db):
        self.db = db

    def get(month):
        hr_final_day_month = HrFinalDayMonthModel.query.filter_by(id=month).first()

        return hr_final_day_month