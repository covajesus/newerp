from io import BytesIO
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.classes.survey_class import SurveyClass, SURVEY_ROL_FULL_STATUS_ACCESS
from app.backend.auth.auth_user import get_current_active_user
from app.backend.db.models import UserModel, SurveyModel

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
    session_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Genera y descarga un .docx con la encuesta (preguntas) y todas las respuestas.
    """
    row = db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")
    if row.status_id != 1 and getattr(session_user, "rol_id", None) != SURVEY_ROL_FULL_STATUS_ACCESS:
        raise HTTPException(
            status_code=403,
            detail="No tiene permiso para generar el documento de encuestas inactivas. "
            "Solo el rol autorizado puede hacerlo; otros roles (p. ej. rol 7) solo con encuesta activa (status_id 1).",
        )

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
