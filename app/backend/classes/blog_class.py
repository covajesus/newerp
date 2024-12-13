from app.backend.db.models import BlogModel
from datetime import datetime
from sqlalchemy import func



class BlogClass:
    def __init__(self, db):
        self.db = db

    def update(self, data):
        blog = self.db.query(BlogModel).first()
        blog.title = data.title
        blog.description = data.description
        blog.added_date = datetime.now()
        blog.updated_date = datetime.now()
        
        self.db.commit()

        return 1
    
    def get_all(self):
        blog = self.db.query(BlogModel).all()
        return blog
    
    def store(self, data, file):
        blog  = BlogModel()
        blog.title = data.title
        blog.description = data.description
        blog.picture = file
        blog.added_date = datetime.now()
        blog.updated_date = datetime.now()

        self.db.add(blog)
        self.db.commit()
        return 1
    
    def delete(self, id):
        blog = self.db.query(BlogModel).filter(BlogModel.id == id).first()
        self.db.delete(blog)
        self.db.commit()
        return 1
    
    