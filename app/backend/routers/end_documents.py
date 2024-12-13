from fastapi import APIRouter, Depends, Response
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.schemas import EndDocument,ContractDatum, UploadContract, UserLogin, SelectDocumentEmployee, IndemnityYear, SubstituteCompensation, FertilityProportional
from app.backend.classes.document_employee_class import DocumentEmployeeClass
from app.backend.classes.end_document_class import EndDocumentClass 
from app.backend.classes.dropbox_class import DropboxClass
from app.backend.auth.auth_user import get_current_active_user
import os
import requests

end_documents = APIRouter(
    prefix="/end_documents",
    tags=["EndDocument"]
)

@end_documents.post("/")
def index(select_document_employee: SelectDocumentEmployee, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EndDocumentClass(db).get_all(select_document_employee.rut)

    return {"message": data}

@end_documents.post("/store")
def store(inputs:EndDocument, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    end_document_inputs = inputs.dict()
    document_id = DocumentEmployeeClass(db).store(end_document_inputs)
    data = EndDocumentClass(db).store(end_document_inputs, document_id)

    return {"message": data}

@end_documents.delete("/delete/{id}")
def delete(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_employee = DocumentEmployeeClass(db).get("id", id)
    response = DocumentEmployeeClass(db).delete(id)

    if response == 1:
        if document_employee.support != None:
            response = DropboxClass(db).delete('/contracts/', document_employee.support)

        if response == 1:
            data = 1
        else:
            data = 0
    else:
        data = 0
    
    return {"message": data}

@end_documents.post("/upload")
def upload(form_data: UploadContract = Depends(UploadContract), session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    dropbox_client = DropboxClass(db)

    filename = dropbox_client.upload(name=form_data.rut, description='contrato', data=form_data.support,
                                 dropbox_path='/contracts/', computer_path=os.path.join(os.path.dirname(__file__)))
    
    data = DocumentEmployeeClass(db).update_file(form_data.id, filename)

    return {"message": data}

@end_documents.get("/download/{id}")
def download(id:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    document_employee = DocumentEmployeeClass(db).get("id", id)
    response = DropboxClass(db).get('/contracts/', document_employee.support)

    response = requests.get(response)
    
    content_disposition = "attachment; filename="+ str(document_employee.support) +""

    return Response(content=response.content, headers={"Content-Disposition": content_disposition})

@end_documents.post("/indemnity_years")
def indemnity_years(inputs:IndemnityYear, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    indemnity_year_inputs = inputs.dict()
    data  = EndDocumentClass(db).indemnity_years(indemnity_year_inputs)

    return {"message": data}

@end_documents.post("/substitute_compensation")
def substitute_compensation(inputs:SubstituteCompensation, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    substitute_compesation_inputs = inputs.dict()
    data  = EndDocumentClass(db).substitute_compensation(substitute_compesation_inputs)

    return {"message": data}

@end_documents.post("/human_resources/end_document/fertility_proportional")
def fertility_proportional(inputs:FertilityProportional, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    fertility_proportional_inputs = inputs.dict() 

    data  = EndDocumentClass(db).fertility_proportional(fertility_proportional_inputs)
    total = EndDocumentClass(db).total_vacations(fertility_proportional_inputs)
    return {"message": data, 'total': total}

@end_documents.get("/edit/{rut}")
def edit(rut:int, session_user: UserLogin = Depends(get_current_active_user), db: Session = Depends(get_db)):
    data = EndDocumentClass(db).get_all(rut)

    return {"message": data}