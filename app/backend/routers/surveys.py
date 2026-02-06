from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.survey_class import SurveyClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import (
    UserLogin,
    SurveyQuestionOption,
    SurveyQuestion,
    SurveyCreate,
    SurveyUpdate,
    SurveyQuestionCreate,
    SurveyQuestionUpdate,
    SurveyResponseItem,
    SurveyResponse
)

surveys = APIRouter(
    prefix="/surveys",
    tags=["Surveys"]
)

# ========== SURVEY ENDPOINTS ==========

@surveys.get("/")
def get_all_surveys(
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las encuestas"""
    try:
        data = SurveyClass(db).get_all_surveys()
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.get("/{survey_id}")
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una encuesta con sus preguntas y opciones"""
    try:
        data = SurveyClass(db).get_survey(survey_id)
        if data.get("status") == "error":
            raise HTTPException(status_code=404, detail=data.get("message"))
        return {"message": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.post("/")
def create_survey(
    survey: SurveyCreate,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva encuesta con sus preguntas y opciones"""
    try:
        survey_data = {
            "title": survey.title,
            "description": survey.description,
            "questions": [
                {
                    "question": q.question,
                    "field_type": q.field_type,
                    "order": q.order,
                    "options": [{"option_text": opt.option_text, "order": opt.order} for opt in (q.options or [])]
                }
                for q in survey.questions
            ]
        }
        result = SurveyClass(db).store_survey(survey_data)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.patch("/{survey_id}")
def update_survey(
    survey_id: int,
    survey: SurveyUpdate,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza una encuesta"""
    try:
        survey_data = {}
        if survey.title is not None:
            survey_data["title"] = survey.title
        if survey.description is not None:
            survey_data["description"] = survey.description
        
        result = SurveyClass(db).update_survey(survey_id, survey_data)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.delete("/{survey_id}")
def delete_survey(
    survey_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Elimina una encuesta"""
    try:
        result = SurveyClass(db).delete_survey(survey_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== QUESTION ENDPOINTS ==========

@surveys.post("/{survey_id}/questions")
def add_question(
    survey_id: int,
    question: SurveyQuestionCreate,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Agrega una pregunta a una encuesta"""
    try:
        question_data = {
            "question": question.question,
            "field_type": question.field_type,
            "order": question.order,
            "options": [{"option_text": opt.option_text, "order": opt.order} for opt in (question.options or [])]
        }
        result = SurveyClass(db).add_question(survey_id, question_data)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.patch("/questions/{question_id}")
def update_question(
    question_id: int,
    question: SurveyQuestionUpdate,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza una pregunta"""
    try:
        question_data = {}
        if question.question is not None:
            question_data["question"] = question.question
        if question.field_type is not None:
            question_data["field_type"] = question.field_type
        if question.order is not None:
            question_data["order"] = question.order
        if question.options is not None:
            question_data["options"] = [{"option_text": opt.option_text, "order": opt.order} for opt in question.options]
        
        result = SurveyClass(db).update_question(question_id, question_data)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Elimina una pregunta"""
    try:
        result = SurveyClass(db).delete_question(question_id)
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== RESPONSE ENDPOINTS ==========

@surveys.post("/responses")
def submit_response(
    response: SurveyResponse,
    db: Session = Depends(get_db)
):
    """Envía las respuestas de una encuesta (público, sin autenticación)"""
    try:
        responses_data = [
            {
                "question_id": r.question_id,
                "answer_text": r.answer_text,
                "option_id": r.option_id
            }
            for r in response.responses
        ]
        result = SurveyClass(db).submit_response(response.survey_id, responses_data)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return {"message": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.get("/{survey_id}/responses")
def get_survey_responses(
    survey_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las respuestas de una encuesta"""
    try:
        data = SurveyClass(db).get_survey_responses(survey_id)
        if isinstance(data, dict) and data.get("status") == "error":
            raise HTTPException(status_code=404, detail=data.get("message"))
        return {"message": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
