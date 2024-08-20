from app.backend.db.models import NewModel
from datetime import datetime
from app.backend.classes.helper_class import HelperClass
from app.backend.classes.dropbox_class import DropboxClass
import markdown

class NewClass:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        try:
            data = self.db.query(NewModel).order_by(NewModel.id).all()
            if not data:
                return "No data found"
            return data
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def get(self, field, value):
        try:
            new = self.db.query(NewModel).filter(getattr(NewModel, field) == value).first()

            dropbox_client = DropboxClass(self.db)

            filename = dropbox_client.get('/news', new.picture)

            return {
                "data": new,
                "image": filename
            }
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"
    
    def store(self, new_inputs, file):
        description = HelperClass().remove_from_string("#", new_inputs.description)
        description = HelperClass().remove_from_string("##", new_inputs.description)
        description = HelperClass().remove_from_string("###", new_inputs.description)
        description = HelperClass().remove_from_string("####", new_inputs.description)
        description = HelperClass().remove_from_string("#####", new_inputs.description)
        description = HelperClass().remove_from_string("######", new_inputs.description)
        description = HelperClass().remove_from_string("**", new_inputs.description)

        new = NewModel()
        new.title = new_inputs.title
        new.description = description
        new.markdown_description = markdown.markdown(new_inputs.description)
        new.picture = file
        new.added_date = datetime.now()
        new.updated_date = datetime.now()

        try:
            self.db.add(new)
            self.db.commit()

            return 1
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"

    def delete(self, id):
        try:
            data = self.db.query(NewModel).filter(NewModel.id == id).first()
            if data:
                self.db.delete(data)
                self.db.commit()
                return 1
            else:
                return 0
        except Exception as e:
            error_message = str(e)
            return f"Error: {error_message}"