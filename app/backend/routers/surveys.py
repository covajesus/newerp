from fastapi import APIRouter, Depends, HTTPException
from app.backend.db.database import get_db
from sqlalchemy.orm import Session
from app.backend.classes.survey_class import SurveyClass, SURVEY_ROL_FULL_STATUS_ACCESS
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.models import UserModel
from app.backend.schemas import (
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


def _assert_can_read_survey_inactive(session_user: UserModel, survey_status_id: int | None) -> None:
    """
    Encuesta activa (status_id == 1): cualquier usuario autorizado (p. ej. rol 7) puede verla.
    Otro status: solo rol SURVEY_ROL_FULL_STATUS_ACCESS (2). El rol 7 no ve encuestas inactivas.
    """
    if survey_status_id == 1:
        return
    if getattr(session_user, "rol_id", None) == SURVEY_ROL_FULL_STATUS_ACCESS:
        return
    raise HTTPException(
        status_code=403,
        detail="No tiene permiso para acceder a encuestas inactivas o no publicadas. "
        "Solo el rol autorizado puede verlas; las demás cuentas (p. ej. rol 7) solo ven encuestas activas.",
    )


# ========== SURVEY ENDPOINTS ==========

@surveys.get("/")
def get_all_surveys(
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Listado: solo rol SURVEY_ROL_FULL_STATUS_ACCESS (2) ve todos los status_id.
    Rol 7 y cualquier otro rol: únicamente encuestas con status_id == 1 (activas).
    """
    try:
        rid = getattr(session_user, "rol_id", None)
        include_all = rid == SURVEY_ROL_FULL_STATUS_ACCESS
        data = SurveyClass(db).get_all_surveys(include_all_statuses=include_all)
        return {"message": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.get("/{survey_id}")
def get_survey(
    survey_id: int,
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene una encuesta con sus preguntas y opciones"""
    try:
        data = SurveyClass(db).get_survey(survey_id)
        if data.get("status") == "error":
            raise HTTPException(status_code=404, detail=data.get("message"))
        _assert_can_read_survey_inactive(session_user, data.get("status_id"))
        return {"message": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@surveys.post("/")
def create_survey(
    survey: SurveyCreate,
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva encuesta con sus preguntas y opciones"""
    try:
        survey_data = {
            "title": survey.title,
            "description": survey.description,
            "branch_office_id": survey.branch_office_id,
            "status_id": survey.status_id,
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
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza una encuesta"""
    try:
        survey_data = {}
        if survey.title is not None:
            survey_data["title"] = survey.title
        if survey.description is not None:
            survey_data["description"] = survey.description
        if survey.branch_office_id is not None:
            survey_data["branch_office_id"] = survey.branch_office_id
        if survey.status_id is not None:
            survey_data["status_id"] = survey.status_id

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
    session_user: UserModel = Depends(get_current_active_user),
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
    session_user: UserModel = Depends(get_current_active_user),
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
    session_user: UserModel = Depends(get_current_active_user),
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
    session_user: UserModel = Depends(get_current_active_user),
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
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las respuestas de una encuesta"""
    try:
        meta = SurveyClass(db).get_survey(survey_id)
        if isinstance(meta, dict) and meta.get("status") == "error":
            raise HTTPException(status_code=404, detail=meta.get("message"))
        _assert_can_read_survey_inactive(session_user, meta.get("status_id"))

        data = SurveyClass(db).get_survey_responses(survey_id)
        if isinstance(data, dict) and data.get("status") == "error":
            raise HTTPException(status_code=404, detail=data.get("message"))
        return {"message": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
