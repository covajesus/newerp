from app.backend.db.models import SurveyModel, SurveyQuestionModel, SurveyQuestionOptionModel, SurveyResponseAnswerModel
from datetime import datetime
import json

class SurveyClass:
    def __init__(self, db):
        self.db = db

    # ========== SURVEYS ==========
    
    def get_all_surveys(self):
        """Obtiene todas las encuestas"""
        try:
            surveys = self.db.query(SurveyModel).order_by(SurveyModel.created_at.desc()).all()
            return [{
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "created_at": survey.created_at.isoformat() if survey.created_at else None,
                "updated_at": survey.updated_at.isoformat() if survey.updated_at else None
            } for survey in surveys]
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_survey(self, survey_id):
        """Obtiene una encuesta con sus preguntas y opciones"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            # Obtener preguntas ordenadas
            questions = self.db.query(SurveyQuestionModel).filter(
                SurveyQuestionModel.survey_id == survey_id
            ).order_by(SurveyQuestionModel.order).all()
            
            questions_data = []
            for question in questions:
                question_dict = {
                    "id": question.id,
                    "question": question.question,
                    "field_type": question.field_type,
                    "order": question.order
                }
                
                # Si la pregunta tiene opciones (select, radio, checkbox), obtenerlas
                if question.field_type in ['select', 'radio', 'checkbox']:
                    options = self.db.query(SurveyQuestionOptionModel).filter(
                        SurveyQuestionOptionModel.question_id == question.id
                    ).order_by(SurveyQuestionOptionModel.order).all()
                    
                    question_dict["options"] = [{
                        "id": option.id,
                        "option_text": option.option_text,
                        "order": option.order
                    } for option in options]
                
                questions_data.append(question_dict)
            
            return {
                "id": survey.id,
                "title": survey.title,
                "description": survey.description,
                "created_at": survey.created_at.isoformat() if survey.created_at else None,
                "updated_at": survey.updated_at.isoformat() if survey.updated_at else None,
                "questions": questions_data
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def store_survey(self, survey_data):
        """Crea una nueva encuesta con sus preguntas y opciones"""
        try:
            # Crear la encuesta
            survey = SurveyModel(
                title=survey_data.get("title"),
                description=survey_data.get("description")
            )
            self.db.add(survey)
            self.db.flush()  # Para obtener el ID
            
            # Crear las preguntas
            questions_data = survey_data.get("questions", [])
            for question_data in questions_data:
                question = SurveyQuestionModel(
                    survey_id=survey.id,
                    question=question_data.get("question"),
                    field_type=question_data.get("field_type", "text"),
                    order=question_data.get("order", 0)
                )
                self.db.add(question)
                self.db.flush()  # Para obtener el ID
                
                # Si la pregunta tiene opciones, crearlas
                if question.field_type in ['select', 'radio', 'checkbox']:
                    options_data = question_data.get("options", [])
                    for option_data in options_data:
                        option = SurveyQuestionOptionModel(
                            question_id=question.id,
                            option_text=option_data.get("option_text"),
                            order=option_data.get("order", 0)
                        )
                        self.db.add(option)
            
            self.db.commit()
            return {"status": "success", "message": "Survey created successfully", "survey_id": survey.id}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def update_survey(self, survey_id, survey_data):
        """Actualiza una encuesta"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            survey.title = survey_data.get("title", survey.title)
            survey.description = survey_data.get("description", survey.description)
            survey.updated_at = datetime.utcnow()
            
            self.db.commit()
            return {"status": "success", "message": "Survey updated successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def delete_survey(self, survey_id):
        """Elimina una encuesta (cascade elimina preguntas, opciones y respuestas)"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            self.db.delete(survey)
            self.db.commit()
            return {"status": "success", "message": "Survey deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    # ========== QUESTIONS ==========
    
    def add_question(self, survey_id, question_data):
        """Agrega una pregunta a una encuesta"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            question = SurveyQuestionModel(
                survey_id=survey_id,
                question=question_data.get("question"),
                field_type=question_data.get("field_type", "text"),
                order=question_data.get("order", 0)
            )
            self.db.add(question)
            self.db.flush()
            
            # Si la pregunta tiene opciones, crearlas
            if question.field_type in ['select', 'radio', 'checkbox']:
                options_data = question_data.get("options", [])
                for option_data in options_data:
                    option = SurveyQuestionOptionModel(
                        question_id=question.id,
                        option_text=option_data.get("option_text"),
                        order=option_data.get("order", 0)
                    )
                    self.db.add(option)
            
            self.db.commit()
            return {"status": "success", "message": "Question added successfully", "question_id": question.id}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def update_question(self, question_id, question_data):
        """Actualiza una pregunta"""
        try:
            question = self.db.query(SurveyQuestionModel).filter(SurveyQuestionModel.id == question_id).first()
            if not question:
                return {"status": "error", "message": "Question not found"}
            
            question.question = question_data.get("question", question.question)
            question.field_type = question_data.get("field_type", question.field_type)
            question.order = question_data.get("order", question.order)
            question.updated_at = datetime.utcnow()
            
            # Si cambió el tipo y ahora tiene opciones, crearlas
            if question.field_type in ['select', 'radio', 'checkbox']:
                options_data = question_data.get("options", [])
                # Eliminar opciones existentes
                self.db.query(SurveyQuestionOptionModel).filter(
                    SurveyQuestionOptionModel.question_id == question_id
                ).delete()
                # Crear nuevas opciones
                for option_data in options_data:
                    option = SurveyQuestionOptionModel(
                        question_id=question_id,
                        option_text=option_data.get("option_text"),
                        order=option_data.get("order", 0)
                    )
                    self.db.add(option)
            
            self.db.commit()
            return {"status": "success", "message": "Question updated successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def delete_question(self, question_id):
        """Elimina una pregunta (cascade elimina opciones y respuestas)"""
        try:
            question = self.db.query(SurveyQuestionModel).filter(SurveyQuestionModel.id == question_id).first()
            if not question:
                return {"status": "error", "message": "Question not found"}
            
            self.db.delete(question)
            self.db.commit()
            return {"status": "success", "message": "Question deleted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    # ========== RESPONSES ==========
    
    def submit_response(self, survey_id, responses_data):
        """Guarda las respuestas de una encuesta"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            # responses_data es una lista de objetos: [{"question_id": 1, "answer_text": "...", "option_id": null}, ...]
            for response_data in responses_data:
                question_id = response_data.get("question_id")
                answer_text = response_data.get("answer_text")
                option_id = response_data.get("option_id")
                
                # Validar que la pregunta pertenezca a la encuesta
                question = self.db.query(SurveyQuestionModel).filter(
                    SurveyQuestionModel.id == question_id,
                    SurveyQuestionModel.survey_id == survey_id
                ).first()
                
                if not question:
                    continue  # Saltar si la pregunta no existe o no pertenece a la encuesta
                
                # Validar que si es opción, el option_id sea válido
                if option_id:
                    option = self.db.query(SurveyQuestionOptionModel).filter(
                        SurveyQuestionOptionModel.id == option_id,
                        SurveyQuestionOptionModel.question_id == question_id
                    ).first()
                    if not option:
                        continue  # Saltar si la opción no existe o no pertenece a la pregunta
                
                # Crear la respuesta
                answer = SurveyResponseAnswerModel(
                    survey_id=survey_id,
                    question_id=question_id,
                    answer_text=answer_text,
                    option_id=option_id
                )
                self.db.add(answer)
            
            self.db.commit()
            return {"status": "success", "message": "Response submitted successfully"}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
    
    def get_survey_responses(self, survey_id):
        """Obtiene todas las respuestas de una encuesta"""
        try:
            survey = self.db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
            if not survey:
                return {"status": "error", "message": "Survey not found"}
            
            responses = self.db.query(SurveyResponseAnswerModel).filter(
                SurveyResponseAnswerModel.survey_id == survey_id
            ).order_by(SurveyResponseAnswerModel.created_at).all()
            
            return [{
                "id": response.id,
                "question_id": response.question_id,
                "answer_text": response.answer_text,
                "option_id": response.option_id,
                "created_at": response.created_at.isoformat() if response.created_at else None
            } for response in responses]
        except Exception as e:
            return {"status": "error", "message": str(e)}
