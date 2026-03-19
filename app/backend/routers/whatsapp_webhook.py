"""
Webhook WhatsApp Cloud API (Meta).

Configuración en Meta Developer:
1. Crear app → WhatsApp → API de prueba o producción.
2. URL de devolución de llamada: https://TU_DOMINIO/api/whatsapp/webhook
3. Token de verificación: el mismo valor que WHATSAPP_VERIFY_TOKEN en .env
4. Suscribirse a messages

Variables .env:
- WHATSAPP_VERIFY_TOKEN (token que configuras en Meta para verificar el webhook GET)
- LIBREDTE_TOKEN (mismo que ya usa WhatsappClass para enviar mensajes Graph)
"""
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.backend.db.database import get_db
from app.backend.classes.whatsapp_admin_bot_class import handle_webhook_payload

# Ruta final: GET/POST /api/whatsapp/webhook (coincide con la URL que pide Meta)
whatsapp_webhook = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Webhook"])


@whatsapp_webhook.get("/webhook")
async def verify_webhook(
    request: Request,
):
    """
    Verificación requerida por Meta al configurar el webhook (challenge).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

    if mode == "subscribe" and token and verify_token and token == verify_token:
        return PlainTextResponse(content=str(challenge or ""), status_code=200)
    raise HTTPException(status_code=403, detail="Verification failed")


@whatsapp_webhook.post("/webhook")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Recibe eventos de WhatsApp (mensajes entrantes).
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    # Meta envía confirmaciones sin messages a veces
    handle_webhook_payload(db, payload)
    return {"status": "ok"}
