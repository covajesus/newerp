from io import BytesIO
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.classes.survey_class import SurveyClass
from app.backend.auth.auth_user import get_current_active_user
from app.backend.schemas import UserLogin

documents = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def _safe_filename_part(text: str, max_len: int = 80) -> str:
    if not text:
        return "encuesta"
    s = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())[:max_len]
    return s or "encuesta"


@documents.get("/generate/{survey_id}")
def generate_survey_word(
    survey_id: int,
    session_user: UserLogin = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Genera y descarga un .docx con la encuesta (preguntas) y todas las respuestas.
    """
    svc = SurveyClass(db)
    data, err = svc.export_survey_results_docx(survey_id)
    if err or data is None:
        low = (err or "").lower()
        code = 404 if ("not found" in low or "no encontrada" in low or "survey not found" in low) else 500
        raise HTTPException(status_code=code, detail=err or "Error al generar documento")

    survey = svc.get_survey(survey_id)
    title_part = "encuesta"
    if isinstance(survey, dict) and survey.get("title") and survey.get("status") != "error":
        title_part = _safe_filename_part(str(survey["title"]))

    filename = f"{title_part}_{survey_id}.docx"
    buf = BytesIO(data)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
