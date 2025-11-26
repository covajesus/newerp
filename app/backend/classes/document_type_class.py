from app.backend.db.models import DocumentTypeModel

class DocumentTypeClass:
    def __init__(self, db):
        self.db = db

    def get_all(self, document_group_id = None):
        try:
            if document_group_id != None:
                data = self.db.query(DocumentTypeModel).filter(DocumentTypeModel.document_group_id == document_group_id).order_by(DocumentTypeModel.document_type).all()
            else:
                data = self.db.query(DocumentTypeModel).order_by(DocumentTypeModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            data = self.db.query(DocumentTypeModel).filter(getattr(DocumentTypeModel, field) == value).first()
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, DocumentType_inputs):
        try:
            data = DocumentTypeModel(**DocumentType_inputs)
            self.db.add(data)
            self.db.commit()
            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def delete(self, id):
        try:
            data = self.db.query(DocumentTypeModel).filter(DocumentTypeModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return "No data found"
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
        
    def update(self, id, DocumentType):
        existing_document_type = self.db.query(DocumentTypeModel).filter(DocumentTypeModel.id == id).one_or_none()

        if not existing_document_type:
            return "No data found"

        existing_document_type_data = DocumentType.dict(exclude_unset=True)
        for key, value in existing_document_type_data.items():
            setattr(existing_document_type, key, value)

        self.db.commit()

        return 1