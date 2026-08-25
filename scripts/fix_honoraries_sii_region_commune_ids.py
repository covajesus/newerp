"""
Actualiza honoraries.region_id / commune_id a códigos SII
(sii_regions.id / sii_communes.id) usando el vínculo commune_id.
Idempotente: no toca filas que ya tienen códigos SII.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.backend.db.database import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        before = db.execute(
            text(
                """
                SELECT COUNT(*) FROM honoraries h
                JOIN sii_communes sc ON sc.commune_id = h.commune_id
                WHERE h.commune_id <> sc.id
                """
            )
        ).scalar()
        print(f"honoraries a migrar (IntraJIS -> SII): {before}")

        result = db.execute(
            text(
                """
                UPDATE honoraries h
                INNER JOIN sii_communes sc ON sc.commune_id = h.commune_id
                SET
                  h.commune_id = sc.id,
                  h.region_id = sc.sii_region_id
                WHERE h.commune_id <> sc.id
                """
            )
        )
        db.commit()
        print(f"filas actualizadas: {result.rowcount}")

        # Fallback: region SII por región IntraJIS si aún queda region_id=0 (RM)
        # pero commune ya es SII
        leftover_rm = db.execute(
            text(
                """
                UPDATE honoraries h
                INNER JOIN sii_communes sc ON sc.id = h.commune_id
                SET h.region_id = sc.sii_region_id
                WHERE h.region_id <> sc.sii_region_id
                """
            )
        )
        db.commit()
        print(f"regiones alineadas a comuna SII: {leftover_rm.rowcount}")

        still_intrajis = db.execute(
            text(
                """
                SELECT COUNT(*) FROM honoraries h
                JOIN communes c ON c.id = h.commune_id
                LEFT JOIN sii_communes sc ON sc.id = h.commune_id
                WHERE sc.id IS NULL
                """
            )
        ).scalar()
        print(f"honoraries aún con commune IntraJIS (sin mapear): {still_intrajis}")

        sample = db.execute(
            text(
                """
                SELECT id, region_id, commune_id
                FROM honoraries
                ORDER BY id DESC
                LIMIT 8
                """
            )
        ).fetchall()
        print("sample post-migración:")
        for row in sample:
            print(" ", row)
    finally:
        db.close()


if __name__ == "__main__":
    main()
