#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Marca NC Campusano y boleta original como emitidas/anuladas."""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

from app.backend.classes.folio_class import FolioClass
from app.backend.db.database import SessionLocal
from app.backend.db.models import DteModel

NC_DTE_ID = 11806644
BOLETA_DTE_ID = 11806289


def main():
    db = SessionLocal()
    try:
        nc = db.query(DteModel).filter(DteModel.id == NC_DTE_ID).first()
        boleta = db.query(DteModel).filter(DteModel.id == BOLETA_DTE_ID).first()
        if not nc or not boleta:
            raise SystemExit(f"missing dtes nc={nc} boleta={boleta}")

        folio_cls = FolioClass(db)
        folio_res = folio_cls.reserve_next_by_document_type(
            61, branch_office_id=boleta.branch_office_id
        )
        if folio_res.get("status") != "success":
            raise SystemExit(folio_res)
        nc_folio = int(folio_res["folio"])
        now = datetime.now()

        nc.folio = nc_folio
        nc.status_id = 5
        nc.denied_folio = str(boleta.folio)
        nc.reason_id = nc.reason_id or 2
        nc.dte_version_id = 1
        nc.updated_date = now

        boleta.status_id = 5
        boleta.denied_folio = str(nc_folio)
        boleta.reason_id = nc.reason_id or 2
        boleta.comment = f"Folio de la Nota de Crédito {nc_folio}"
        boleta.updated_date = now

        db.add(nc)
        db.add(boleta)
        db.commit()

        folio_cls.bind_folio_to_dte(
            folio_res["id"],
            nc.id,
            branch_office_id=boleta.branch_office_id,
        )

        db.refresh(nc)
        db.refresh(boleta)
        print("NC:", {
            "id": nc.id,
            "folio": nc.folio,
            "status_id": nc.status_id,
            "denied_folio": nc.denied_folio,
            "total": nc.total,
            "rut": nc.rut,
        })
        print("BOLETA:", {
            "id": boleta.id,
            "folio": boleta.folio,
            "status_id": boleta.status_id,
            "denied_folio": boleta.denied_folio,
            "reason_id": boleta.reason_id,
            "comment": boleta.comment,
            "total": boleta.total,
        })
        print("folio_row:", folio_res)
    finally:
        db.close()


if __name__ == "__main__":
    main()
