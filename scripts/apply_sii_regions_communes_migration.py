"""
Crea tablas nuevas sii_regions / sii_communes y las puebla desde el catálogo SII BTE.
No modifica el esquema de regions ni communes.
"""
from __future__ import annotations

import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# Permitir ejecución directa: python scripts/apply_sii_regions_communes_migration.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.backend.classes.sii.bte_communes import REGIONS, regions_list
from app.backend.db.database import SessionLocal
from app.backend.db.models import CommuneModel, RegionModel, SiiCommuneModel, SiiRegionModel


def _normalize(name: str) -> str:
    text_value = unicodedata.normalize("NFKD", (name or "").strip().upper())
    text_value = "".join(c for c in text_value if not unicodedata.combining(c))
    return " ".join(text_value.replace("-", " ").split())


def _match_keys(name: str) -> set[str]:
    """Claves flexibles solo para el seed (vincular commune_id)."""
    normalized = _normalize(name)
    keys = {normalized, normalized.replace(" ", "")}
    stop = {"DE", "DEL", "LA", "LAS", "LOS", "EL"}
    tokens = [t for t in normalized.split() if t not in stop]
    if tokens:
        joined = " ".join(tokens)
        keys.add(joined)
        keys.add(joined.replace(" ", ""))
        compact = []
        for t in tokens:
            if t == "ESTACION":
                compact.append("EST")
            elif t == "PEDRO":
                compact.append("P")
            else:
                compact.append(t)
        compact_s = " ".join(compact)
        keys.add(compact_s)
        keys.add(compact_s.replace(" ", ""))
    return {k for k in keys if k}


DDL = [
    """
    CREATE TABLE IF NOT EXISTS sii_regions (
      id INT NOT NULL,
      name VARCHAR(255) NOT NULL,
      region_id INT DEFAULT NULL,
      added_date DATETIME DEFAULT NULL,
      updated_date DATETIME DEFAULT NULL,
      PRIMARY KEY (id),
      KEY idx_sii_regions_region_id (region_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS sii_communes (
      id INT NOT NULL,
      sii_region_id INT NOT NULL,
      name VARCHAR(255) NOT NULL,
      name_normalized VARCHAR(255) DEFAULT NULL,
      commune_id INT DEFAULT NULL,
      added_date DATETIME DEFAULT NULL,
      updated_date DATETIME DEFAULT NULL,
      PRIMARY KEY (id),
      KEY idx_sii_communes_region (sii_region_id),
      KEY idx_sii_communes_commune_id (commune_id),
      KEY idx_sii_communes_name_norm (name_normalized)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def ensure_tables(db) -> None:
    for stmt in DDL:
        db.execute(text(stmt))
    db.commit()
    print("tables ok: sii_regions, sii_communes")


def seed(db) -> None:
    now = datetime.now()
    labels = {item["id"]: item["name"] for item in regions_list()}

    # Map IntraJIS region by simplefactura_region_code (y fallback id==código SII)
    intrajis_regions = db.query(RegionModel).all()
    by_sf = {
        int(r.simplefactura_region_code): r
        for r in intrajis_regions
        if r.simplefactura_region_code is not None
    }
    by_id = {int(r.id): r for r in intrajis_regions}

    region_count = 0
    for sii_id, communes in REGIONS.items():
        name = labels.get(sii_id, f"Región {sii_id}")
        linked = by_sf.get(int(sii_id)) or by_id.get(int(sii_id))
        row = db.query(SiiRegionModel).filter(SiiRegionModel.id == sii_id).first()
        if not row:
            row = SiiRegionModel(id=sii_id, added_date=now)
            db.add(row)
        row.name = name
        row.region_id = int(linked.id) if linked else None
        row.updated_date = now
        region_count += 1

    db.flush()

    # Index IntraJIS communes by region for linking
    communes = db.query(CommuneModel).all()
    by_region: dict[int, list[CommuneModel]] = {}
    for c in communes:
        by_region.setdefault(int(c.region_id) if c.region_id is not None else -1, []).append(c)

    commune_count = 0
    linked_count = 0
    unmatched = []

    for sii_region_id, commune_map in REGIONS.items():
        sii_region = db.query(SiiRegionModel).filter(SiiRegionModel.id == sii_region_id).first()
        candidates = by_region.get(int(sii_region.region_id), []) if sii_region and sii_region.region_id is not None else []
        # También candidatos de region_id 0 cuando SII=13 (RM IntraJIS usa 0)
        if sii_region_id == 13:
            candidates = list({c.id: c for c in (candidates + by_region.get(0, []))}.values())

        candidate_keys: list[tuple[CommuneModel, set[str]]] = [
            (c, _match_keys(c.commune or "")) for c in candidates
        ]

        for code, name in commune_map.items():
            norm = _normalize(name)
            row = db.query(SiiCommuneModel).filter(SiiCommuneModel.id == code).first()
            if not row:
                row = SiiCommuneModel(id=int(code), added_date=now)
                db.add(row)
            row.sii_region_id = int(sii_region_id)
            row.name = name
            row.name_normalized = norm
            row.updated_date = now

            if row.commune_id is None:
                sii_keys = _match_keys(name)
                matched = None
                for c, keys in candidate_keys:
                    if keys & sii_keys:
                        matched = c
                        break
                if matched:
                    row.commune_id = int(matched.id)
                    linked_count += 1
                else:
                    unmatched.append((sii_region_id, code, name))
            else:
                linked_count += 1
            commune_count += 1

    db.commit()
    print(f"seeded regions={region_count} communes={commune_count} linked_commune_id={linked_count}")
    if unmatched:
        print(f"unmatched sii communes (sin commune_id): {len(unmatched)}")
        for item in unmatched[:40]:
            print(" ", item)


def main() -> None:
    db = SessionLocal()
    try:
        ensure_tables(db)
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
