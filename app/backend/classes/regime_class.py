from app.backend.db.models import RegimeModel

class RegimeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(RegimeModel).order_by(RegimeModel.regime).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"