#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Prueba real: boleta v2 chica + NC v2 contra SimpleFactura."""
import json
import os
import sys
from datetime import datetime
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.backend.classes.customer_ticket_class import CustomerTicketClass
from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import BranchOfficeModel


def main():
    db = SessionLocal()
    try:
        cls = CustomerTicketClass(db)
        branch_id = 1
        total = 119

        print("=== 1) Emitir boleta v2 de prueba ($119) ===", flush=True)
        boleta = cls.test_emit_biller_style_v2(total=total, branch_office_id=branch_id)
        print(json.dumps(boleta, default=str, ensure_ascii=False, indent=2), flush=True)
        if boleta.get("status") != "success":
            print("ABORT: no se pudo emitir boleta de prueba; no se intenta NC.", flush=True)
            return

        boleta_folio = boleta.get("folio")
        if not boleta_folio:
            data = boleta.get("data") or {}
            if isinstance(data, dict):
                boleta_folio = data.get("folio") or data.get("Folio")
        if not boleta_folio:
            print("ABORT: boleta emitida pero sin folio en la respuesta.", flush=True)
            return
        boleta_folio = int(boleta_folio)
        print(f"Boleta folio={boleta_folio}", flush=True)

        print("=== 2) Reservar folio NC 61 y emitir NC v2 ===", flush=True)
        folio_res = FolioClass(db).reserve_next_by_document_type(61, branch_office_id=branch_id)
        print("folio_res:", folio_res, flush=True)
        if folio_res.get("status") != "success":
            print("ABORT: no hay folio 61 en pool.", flush=True)
            return

        nc_folio = int(folio_res["folio"])
        branch = db.query(BranchOfficeModel).filter(BranchOfficeModel.id == branch_id).first()
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
            ref_folio=boleta_folio,
            ref_date=datetime.now(),
            gross_amount=total,
            nc_folio=nc_folio,
        )
        print("NC document:", json.dumps(document, ensure_ascii=False, indent=2), flush=True)

        nc = cls.emit_credit_note_v2(document, branch)
        print("=== NC RESULT ===", flush=True)
        print(json.dumps(nc, default=str, ensure_ascii=False, indent=2), flush=True)

        if nc.get("status") != "success":
            FolioClass(db).release_folio_pool_after_failed_emit(
                folio_res["id"],
                folio_number=nc_folio,
                dte_type_id=61,
                emit_result=nc,
                branch_office_id=branch_id,
            )
            print("NC FALLÓ. Folio 61 liberado/marcado según error.", flush=True)
        else:
            print(f"NC OK folio={nc.get('folio') or nc_folio}", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
