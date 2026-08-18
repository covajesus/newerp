#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reintento NC v2 con timeout 90s contra la boleta de prueba 33474920."""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import requests
from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import BranchOfficeModel


def main():
    db = SessionLocal()
    try:
        cls = CustomerTicketClass(db)
        token_res = cls.get_token()
        print("token:", token_res.get("status"), flush=True)
        token = token_res.get("accessToken")
        if not token:
            print(token_res)
            return

        folio_res = FolioClass(db).reserve_next_by_document_type(61, branch_office_id=1)
        print("folio_res:", folio_res, flush=True)
        if folio_res.get("status") != "success":
            return
        nc_folio = int(folio_res["folio"])
        branch = db.query(BranchOfficeModel).filter(BranchOfficeModel.id == 1).first()
        customer_data = {
            "customer_data": {
                "rut": "66666666-6",
                "customer": "Cliente en Sucursal",
                "address": "Matucana 40",
                "commune": "Santiago",
            }
        }
        document = cls._build_subscriber_credit_note_document_v2(
            customer_data,
            branch,
            ref_dte_type=39,
            ref_folio=33474920,
            ref_date=datetime.now(),
            gross_amount=119,
            nc_folio=nc_folio,
        )
        url = "https://api.simplefactura.cl/invoiceCreditDebitNotesV2/Casa_Matriz/6"
        payload = {"Documento": document}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        print("POST", url, "folio", nc_folio, flush=True)
        try:
            r = requests.post(
                url,
                data=json.dumps(payload, ensure_ascii=False),
                headers=headers,
                timeout=90,
            )
            print("HTTP", r.status_code, flush=True)
            print(r.text[:4000], flush=True)
        except Exception as exc:
            print("EXC:", type(exc).__name__, exc, flush=True)
            FolioClass(db).release_folio_pool(folio_res["id"])
            return

        if r.status_code >= 400 or (r.text and '"status": 200' not in r.text and '"status":200' not in r.text):
            FolioClass(db).release_folio_pool_after_failed_emit(
                folio_res["id"],
                folio_number=nc_folio,
                dte_type_id=61,
                emit_result={"status": "error", "message": r.text[:500], "http_status": r.status_code},
                branch_office_id=1,
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
