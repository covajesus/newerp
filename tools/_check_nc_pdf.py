#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
import requests
from app.backend.classes.customer_ticket_class import CustomerTicketClass, SIMPLEFACTURA_RUT_EMISOR, SIMPLEFACTURA_SUCURSAL, SIMPLEFACTURA_AMBIENTE
from app.backend.db.database import SessionLocal

db = SessionLocal()
cls = CustomerTicketClass(db)
token = cls.get_token().get("accessToken")
payload = {
    "credenciales": {
        "rutEmisor": SIMPLEFACTURA_RUT_EMISOR,
        "nombreSucursal": SIMPLEFACTURA_SUCURSAL,
    },
    "dteReferenciadoExterno": {
        "codigoTipoDte": 61,
        "ambiente": SIMPLEFACTURA_AMBIENTE,
        "folio": 6975,
    },
}
r = requests.post(
    "https://api.simplefactura.cl/getPdf",
    json=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    timeout=30,
)
print("HTTP", r.status_code, "len", len(r.content), "pdf", r.content[:8])
if r.status_code != 200:
    print(r.text[:1500])
db.close()
